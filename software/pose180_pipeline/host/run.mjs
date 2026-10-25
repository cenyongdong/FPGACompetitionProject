import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import os from 'node:os';
import { ConfirmedReader, decodeFull, FULL_BYTES } from './full_record.mjs';
import { CreditWindow, BoundedWriter, BufferPool, SendSchedule } from './flow.mjs';
import { BONES } from '../../../demo_v1/host/protocol.mjs';
import { HostDeliveryTiming } from '../../../demo_v1/host/delivery_timing.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE,'../../..');
const clock = () => process.hrtime.bigint();
const sleep = ms => new Promise(resolve => setTimeout(resolve,ms));
const stats = values => {
    if (!values.length) return null;
    const sorted = [...values].sort((a,b) => a-b);
    return {mean:values.reduce((a,b)=>a+b,0)/values.length,p95:sorted[Math.ceil(values.length*.95)-1],p99:sorted[Math.ceil(values.length*.99)-1],max:sorted.at(-1),over_33_333_ms:values.filter(value=>value>1000/30).length};
};

export function prepareArchive(file, bytes) {
    const started = clock(), fd = fs.openSync(file,'wx');
    // ftruncate alone only extends logical EOF. Materialize the entire archive
    // before input admission so allocation/valid-data extension stays outside
    // the per-frame archive ACK path. One scratch block bounds preparation RAM.
    try {
        const zeros = Buffer.alloc(Math.min(1024*1024,bytes));
        for (let offset=0;offset<bytes;) {
            const written=fs.writeSync(fd,zeros,0,Math.min(zeros.length,bytes-offset),offset);
            if (!written) throw new Error('Archive preparation made no progress');
            offset+=written;
        }
        fs.fsyncSync(fd);
        return {fd,preparation:{mode:'full_zero_write_and_fsync_before_ready',bytes,elapsed_ms:Number(clock()-started)/1e6}};
    } catch (error) { fs.closeSync(fd); throw error; }
}

class PayloadPrefetch {
    constructor(count, catalog, files) {
        this.count = count; this.catalog = catalog; this.files = files;
        this.slots = Array.from({length:Math.min(128,count)}, () => ({buffer:Buffer.alloc(86400),index:-1,promise:null}));
    }
    schedule(index) {
        if (index >= this.count) return;
        const slot = this.slots[index % this.slots.length]; slot.index = index; slot.error = null;
        slot.promise = (async () => {
            const sample = this.catalog.samples[index % this.catalog.samples.length], file = this.files[sample.split || 'test'];
            if (!file) throw new Error('Unknown source split');
            const sourceIndex = sample.payload_index ?? sample.index;
            if (!Number.isInteger(sourceIndex) || sourceIndex < 0) throw new Error('Invalid source payload index');
            let offset = 0;
            while (offset < slot.buffer.length) {
                const result = await file.read(slot.buffer,offset,slot.buffer.length-offset,sourceIndex*86400+offset);
                if (!result.bytesRead) throw new Error('Truncated source payload'); offset += result.bytesRead;
            }
        })().catch(error => { slot.error = error; });
    }
    async ready() { for (let i=0;i<this.slots.length;++i) this.schedule(i); await Promise.all(this.slots.map(slot=>slot.promise)); for (const slot of this.slots) if(slot.error) throw slot.error; }
    async copy(index, target) {
        const slot = this.slots[index % this.slots.length];
        if (slot.index !== index) throw new Error('Prefetch ring identity mismatch');
        await slot.promise; if (slot.error) throw slot.error;
        slot.buffer.copy(target,32); this.schedule(index+this.slots.length);
    }
    async close() { await Promise.allSettled(this.slots.map(slot=>slot.promise)); }
}

export async function main(argv = process.argv.slice(2)) {
    const options = {};
    for(let i=0;i<argv.length;i+=2) { if(!argv[i].startsWith('--') || argv[i+1] === undefined) throw new Error('Expected --name value options'); options[argv[i].slice(2)] = argv[i+1]; }
    const stage = options.stage || 'basic', counts = {basic:3,short:900,medium:9000,stress:54000};
    const count = Number(options.count ?? options.frames ?? counts[stage]), hz = Number(options.hz ?? (stage === 'basic' ? 5 : 30));
    const limit = Number(options['max-inflight'] ?? 8), maxAgeMs = Number(options['max-frame-age-ms'] ?? 1000);
    const hdmi = options.hdmi ?? '1';
    if (!['0','1'].includes(hdmi)) throw new Error('Expected --hdmi 0|1');
    const toleranceMs = Number(options['send-tolerance-ms'] ?? 20), linger = Number(options.linger ?? 0);
    const inputPort = Number(options['input-port'] ?? 39382), resultPort = Number(options['result-port'] ?? 39381), httpPort = Number(options['http-port'] ?? 39380);
    if(!Number.isInteger(count)||count<1||count>54000||!Number.isFinite(hz)||hz<=0||hz>60||!Number.isFinite(toleranceMs)||toleranceMs<0||toleranceMs>100||!Number.isFinite(linger)||linger<0||linger>3600) throw new Error('Invalid finite run bound');
    for(const port of [inputPort,resultPort,httpPort]) if(!Number.isInteger(port)||port<1||port>65535) throw new Error('Invalid port');
    const credit = new CreditWindow(limit,maxAgeMs), schedule = new SendSchedule(hz,toleranceMs);
    const data = path.resolve(options.data || path.join(ROOT,'demo_v1/data/mixed'));
    const output = path.resolve(options.output || path.join(ROOT,'software/pose180_pipeline/runs',stage));
    const catalog = JSON.parse(await fs.promises.readFile(path.join(data,'catalog.json'),'utf8'));
    if(!Array.isArray(catalog.samples)||!catalog.samples.length||catalog.payload_bytes!==86400) throw new Error('Invalid aligned source catalog');
    const session = BigInt(Date.now()), stamps = new BigUint64Array(count), delivery = new HostDeliveryTiming(count,clock);
    const latencies=[],processes=[],arrivals=[],queues=[],splitCounts={};
    let sent=0,received=0,rawCount=0,complete=false,error=null,last=null,input=null,resultSocket=null,pacer=null,parser=null,pending=null;
    let rawFd=null,archivePreparation=null,prefetch=null,rawWriter=null,metadataWriter=null,sentWriter=null,tcp=null,server=null,wss=null;
    let ageTimer=null,heartbeat=null,receiveTask=null,sendTask=null,pacerClosed=null,rawRecords=0,rawStarted=false;
    const files={}, errors=[], archiveStreams=[];
    const abort = new AbortController();
    const status = () => ({stage,session:session.toString(),target:count,hz,sent,received,complete,errors,last_frame:last?.frame,connected:!!resultSocket,
        inflight:credit.pending.size,max_inflight:limit,inflight_high:credit.high,max_frame_age_ms:maxAgeMs,strict30Hz:hz===30&&schedule.strict,
        model:'180-query epoch99 / ZG330 / PS',full_schema:'PIWFUL3/3',full_bytes:FULL_BYTES,bones:BONES,HDMI:hdmi==='1',csi_source:'host_simulated'});
    let broadcast = () => {};
    const fail = reason => {
        if (error) return;
        error = reason instanceof Error ? reason : new Error(String(reason)); errors.push(error.message);
        console.error('HOST_STOP',error.message); abort.abort(error); credit.close(error);
        input?.destroy(error); resultSocket?.destroy(error); pacer?.kill(); broadcast({type:'status',status:status()});
    };
    const signal = () => fail(new Error('User cancelled host run'));
    process.once('SIGINT',signal); process.once('SIGTERM',signal);
    async function connectInput() {
        const deadline = Date.now()+30000;
        while(Date.now()<deadline&&!abort.signal.aborted) {
            const socket = new net.Socket();
            try {
                await new Promise((resolve,reject) => { const bad = e => {socket.off('connect',connected);reject(e);}; const connected = () => {socket.off('error',bad);resolve();}; socket.once('error',bad);socket.once('connect',connected);socket.setTimeout(3000,()=>socket.destroy(new Error('Input connection timeout')));socket.connect(inputPort,options['input-host']||'192.168.126.49'); });
                socket.setTimeout(0); return socket;
            } catch(reason) { socket.destroy(); if(!['ECONNREFUSED','ETIMEDOUT'].includes(reason.code) && reason.message!=='Input connection timeout') throw reason; await sleep(100); }
        }
        throw error || new Error('Board input listener startup timeout');
    }
    async function sendInputs() {
        input = await connectInput(); input.setNoDelay(true); input.on('error',fail);
        const networkWriter = new BoundedWriter(input,86432), pool = new BufferPool(2,86432);
        prefetch = new PayloadPrefetch(count,catalog,files); await prefetch.ready();
        pacer = spawn(options['pacer-python'] || 'python',[path.join(HERE,'pacer.py'),String(count),String(hz)],{windowsHide:true,stdio:['pipe','pipe','pipe']});
        pacerClosed = new Promise(resolve=>pacer.once('close',resolve));
        pacer.on('error',fail); pacer.stdin.on('error',reason=>{if(!abort.signal.aborted)fail(reason);});pacer.stderr.on('data',bytes=>{if(!abort.signal.aborted)fail(new Error('Pacer: '+bytes.toString()));});
        try { os.setPriority(pacer.pid,os.constants.priority.PRIORITY_ABOVE_NORMAL); } catch {}
        let index=0,ready=false;
        for await(const line of createInterface({input:pacer.stdout})) {
            if(abort.signal.aborted) break;
            if(!ready) { if(line!=='READY') throw new Error('Pacer handshake differs'); ready=true; schedule.epoch=clock()+200000000n; pacer.stdin.write('GO\n'); continue; }
            if(Number(line)!==index||index>=count) throw new Error('Pacer tick sequence differs');
            await credit.wait();
            // Python performs the high-resolution minimum wait. Node timers can
            // oversleep repeatedly on Windows and cumulatively lower the rate.
            if(clock()+1000000n<schedule.earliest(index))throw new Error('Pacer tick preceded the minimum send time');
            const record=pool.acquire();
            try {
                await prefetch.copy(index,record); if(abort.signal.aborted) throw error;
                const stamp=clock(), planned=schedule.planned(index), late=schedule.mark(index,stamp);
                record.write('PIWCSI2\0',0,'ascii');record.writeUInt32LE(2,8);record.writeUInt32LE(86400,12);record.writeBigUInt64LE(BigInt(1000000+index),16);record.writeBigUInt64LE(stamp,24);
                stamps[index]=stamp;credit.reserve(index,stamp);++sent;
                await networkWriter.write(record); // record remains exclusively owned through callback/drain.
                const sendEnd=clock(),sample=catalog.samples[index%catalog.samples.length];
                await sentWriter.write(Buffer.from(JSON.stringify({frame:1000000+index,sample:sample.name,split:sample.split||'test',planned_ns:planned.toString(),source_ns:stamp.toString(),send_end_ns:sendEnd.toString(),late_ms:late,inflight:credit.pending.size,strict30Hz:hz===30&&schedule.strict})+'\n'));
            } finally { pool.release(record); }
            ++index;
            if(index===count)pacer.stdin.end('NEXT 0\n');
            else {
                await credit.wait();if(abort.signal.aborted)throw error;
                const delayNs=schedule.earliest(index)-clock();
                pacer.stdin.write(`NEXT ${delayNs>0n?delayNs:0n}\n`);
            }
        }
        if(!abort.signal.aborted&&index!==count) throw new Error('Pacer ended before final input');
        if(!abort.signal.aborted) input.end();
    }
    async function receiveResults(socket) {
        parser = new ConfirmedReader(); socket.setNoDelay(true);socket.on('error',fail);
        const ackWriter = new BoundedWriter(socket,8), ack = Buffer.alloc(8);
        for await(const chunk of socket) {
            await parser.push(chunk,async bytes => {
                const ordinal=rawCount++;
                if(ordinal<count){delivery.mark(ordinal,'raw_ready');delivery.mark(ordinal,'save_begin');}
                await rawWriter.write(bytes); ++rawRecords;
                if(ordinal>=count) throw new Error('Unexpected excess complete result (original archived)');
                delivery.mark(ordinal,'save_end');
                // Full original values are now archived, even if decoding/identity rejects them.
                const frame=decodeFull(bytes);delivery.mark(ordinal,'decode_end');
                if(pending||received>=sent||frame.session!==session.toString()||frame.frame!==String(1000000+received)||frame.invocation!==String(received)||frame.sequence!==String(received+1)||frame.source_ns!==stamps[received].toString()) throw new Error('Input/result identity or sequence mismatch');
                pending=frame;
                ack.writeBigUInt64LE(BigInt(frame.sequence));delivery.mark(ordinal,'ack_queued');
                await ackWriter.write(ack);delivery.mark(ordinal,'ack_flushed');
            },async sequence => {
                if(!pending||BigInt(pending.sequence)!==sequence) throw new Error('Board final confirmation differs');
                const frame=pending,now=clock(),elapsed=Number(now-BigInt(frame.source_ns))/1e6;
                delivery.mark(received,'confirmation');
                const sample=catalog.samples[received%catalog.samples.length];frame.sample=sample.name;frame.split=sample.split||'test';frame.end_to_end_ms=elapsed;
                // Metadata has the same bounded callback/drain contract as raw and sent logs.
                await metadataWriter.write(Buffer.from(JSON.stringify({frame:frame.frame,invocation:frame.invocation,sequence:frame.sequence,sample:frame.sample,split:frame.split,pc_received_ns:now.toString(),end_to_end_ms:elapsed,...frame.metrics})+'\n'));
                credit.confirm(received);pending=null;++received;splitCounts[frame.split]=(splitCounts[frame.split]||0)+1;
                latencies.push(elapsed);processes.push(frame.metrics.process_ms);queues.push(frame.metrics.queue_ms);arrivals.push(now);last=frame;broadcast({type:'frame',frame});
            });
        }
        parser.finish();
        if(received!==count||sent!==count) throw new Error('Incomplete live run at result EOF');
    }
    try {
        for(const [split,spec] of Object.entries(catalog.sources||{test:{path:path.join(data,'aligned.bin'),count:catalog.samples.length}})) {
            const file=await fs.promises.open(path.resolve(data,spec.path),'r');files[split]=file;
            if(!Number.isInteger(spec.count)||spec.count<1||(await file.stat()).size!==spec.count*86400) throw new Error('Incomplete aligned source: '+split);
        }
        await fs.promises.mkdir(output,{recursive:false});rawStarted=true;
        const prepared=prepareArchive(path.join(output,'actual.full'),count*FULL_BYTES);
        rawFd=prepared.fd;archivePreparation=prepared.preparation;
        const raw=fs.createWriteStream(path.join(output,'actual.full'),{fd:rawFd,autoClose:false,start:0,highWaterMark:FULL_BYTES});
        const metadata=fs.createWriteStream(path.join(output,'received.jsonl'),{flags:'wx',highWaterMark:65536});
        const sends=fs.createWriteStream(path.join(output,'sent.jsonl'),{flags:'wx',highWaterMark:65536});
        archiveStreams.push(raw,metadata,sends);for(const stream of archiveStreams) stream.on('error',fail);
        rawWriter=new BoundedWriter(raw,FULL_BYTES);metadataWriter=new BoundedWriter(metadata,65536);sentWriter=new BoundedWriter(sends,65536);
        try { os.setPriority(0,os.constants.priority.PRIORITY_ABOVE_NORMAL); } catch {}
        const dependency=path.join(ROOT,'software/pc_viewer/node_modules');
        const {WebSocketServer,WebSocket}=createRequire(import.meta.url)(path.join(dependency,'ws'));
        wss=new WebSocketServer({noServer:true,perMessageDeflate:false,maxPayload:1024});
        broadcast=value=>{const encoded=JSON.stringify(value);for(const client of wss.clients) if(client.readyState===WebSocket.OPEN) {if(client.bufferedAmount>65536)client.terminate();else client.send(encoded);}};
        const assets=new Map([['/','index.html'],['/app.js','app.js'],['/scene.js','scene.js'],['/style.css','style.css']]);
        const vendors=new Map([['/vendor/three.module.js','three/build/three.module.js'],['/vendor/three.core.js','three/build/three.core.js'],['/vendor/OrbitControls.js','three/examples/jsm/controls/OrbitControls.js']]);
        server=http.createServer((request,response)=>{
            if(request.method!=='GET') {response.writeHead(405).end();return;}
            if(request.url==='/api/status'){response.setHeader('Content-Type','application/json');response.end(JSON.stringify(status()));return;}
            const asset=assets.get(request.url),vendor=vendors.get(request.url);if(!asset&&!vendor){response.writeHead(404).end();return;}
            response.setHeader('Cache-Control','no-store');response.setHeader('Content-Type',request.url.endsWith('.js')?'text/javascript':request.url.endsWith('.css')?'text/css':'text/html; charset=utf-8');
            fs.createReadStream(vendor?path.join(dependency,vendor):path.join(ROOT,'demo_v1/web',asset)).on('error',e=>response.destroy(e)).pipe(response);
        });server.on('error',fail);
        server.on('upgrade',(request,socket,head)=>{if(request.url!=='/updates'||request.headers.origin&&request.headers.origin!==`http://127.0.0.1:${httpPort}`){socket.destroy();return;}wss.handleUpgrade(request,socket,head,client=>{client.send(JSON.stringify({type:'status',status:status()}));if(last)client.send(JSON.stringify({type:'frame',frame:last}));});});
        let admit;
        const connected=new Promise((resolve,reject)=>{admit=resolve;abort.signal.addEventListener('abort',()=>reject(error),{once:true});});
        tcp=net.createServer(socket=>{if(resultSocket||abort.signal.aborted){socket.destroy();return;}resultSocket=socket;admit(socket);});tcp.on('error',fail);
        await new Promise((resolve,reject)=>{tcp.once('error',reject);tcp.listen(resultPort,'127.0.0.1',resolve);});
        await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(httpPort,'127.0.0.1',resolve);});
        const runtime={pid:process.pid,session:session.toString(),stage,count,hz,output,data,dataset_sha256:catalog.sha256,input_host:options['input-host']||'192.168.126.49',input_port:inputPort,result_port:resultPort,http_port:httpPort,max_inflight:limit,max_frame_age_ms:maxAgeMs,HDMI:hdmi==='1',archive_preparation:archivePreparation,full_schema:'PIWFUL3/3',full_bytes:FULL_BYTES};
        fs.writeFileSync(path.join(output,'runtime.json'),JSON.stringify(runtime,null,2)+'\n');console.log('HOST_READY',JSON.stringify({...runtime,url:`http://127.0.0.1:${httpPort}`}));
        heartbeat=setInterval(()=>broadcast({type:'status',status:status()}),1000);
        const startup=setTimeout(()=>fail(new Error('Board result connection startup timeout')),60000);
        let socket;try {socket=await connected;}finally{clearTimeout(startup);}
        ageTimer=setInterval(()=>{try{credit.checkAge();}catch(reason){fail(reason);}},10);
        receiveTask=receiveResults(socket).catch(reason=>{fail(reason);throw reason;});
        sendTask=sendInputs().catch(reason=>{fail(reason);throw reason;});
        await Promise.all([receiveTask,sendTask]);if(error)throw error;complete=true;
    } catch(reason) {fail(reason);} finally {
        clearInterval(ageTimer);clearInterval(heartbeat);credit.close(error||new Error('Run complete'));pacer?.kill();
        if(error){input?.destroy();resultSocket?.destroy();}
        await Promise.allSettled([receiveTask,sendTask].filter(Boolean));await prefetch?.close();await pacerClosed;
        const cleanupFailure=reason=>{const message='Cleanup/evidence: '+String(reason.message||reason);errors.push(message);console.error(message);if(!error){error=reason;complete=false;}};
        if(parser?.used&&rawStarted)try{fs.writeFileSync(path.join(output,parser.pending?'confirmation.partial':'actual.partial'),parser.partial());}catch(reason){cleanupFailure(reason);}
        const ending=await Promise.allSettled([rawWriter,metadataWriter,sentWriter].filter(Boolean).map(writer=>writer.end()));
        for(const result of ending) if(result.status==='rejected'&&!error){error=result.reason;errors.push(error.message);complete=false;}
        if(rawFd!==null){try{const bytes=archiveStreams[0]?.bytesWritten||0;fs.ftruncateSync(rawFd,bytes);}catch(reason){cleanupFailure(reason);}finally{try{fs.closeSync(rawFd);}catch(reason){cleanupFailure(reason);}}}
        if(rawStarted)try {
            delivery.save(output);
            const intervals=arrivals.slice(1).map((stamp,index)=>Number(stamp-arrivals[index])/1e6);
            const report={...status(),complete:complete&&!error,all_records_received:complete&&!error&&received===count,raw_records:rawRecords,unconfirmed_records:rawRecords-received,
                unconfirmed_frame:pending?.frame??null,inflight_frames:[...credit.pending.keys()].map(index=>({invocation:index,frame:1000000+index,source_ns:stamps[index].toString()})),
                unique_source_count:Math.min(received,catalog.samples.length),split_counts:splitCounts,dataset_sha256:catalog.sha256,
                input_rate_hz:sent>1?(sent-1)*1e9/Number(stamps[sent-1]-stamps[0]):0,output_rate_hz:received>1?(received-1)*1e9/Number(arrivals.at(-1)-arrivals[0]):0,
                process_ms:stats(processes),end_to_end_ms:stats(latencies),queue_ms:stats(queues),output_interval_ms:stats(intervals),sender_late_ms:stats(schedule.lateness),
                strict30Hz:complete&&!error&&hz===30&&schedule.strict,sender_absolute_epoch_ns:schedule.epoch?.toString()??null,sender_missed_slots:schedule.missed,sender_pause_intervals:schedule.pauses,credit_waits:credit.waits,
                archive_preparation:archivePreparation,archive_write_high_bytes:{raw:rawWriter?.high??0,metadata:metadataWriter?.high??0,sent:sentWriter?.high??0},raw_bytes:fs.statSync(path.join(output,'actual.full')).size,
                strict_33_333ms_processing_pass:complete&&!error&&processes.every(value=>value<=1000/30),strict_33_333ms_end_to_end_pass:complete&&!error&&latencies.every(value=>value<=1000/30)};
            fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(report,null,2)+'\n');console.log('HOST_COMPLETE',JSON.stringify(report));broadcast({type:'status',status:status()});
        }catch(reason){cleanupFailure(reason);}
        if(!error&&linger)await sleep(linger*1000);
        input?.destroy();resultSocket?.destroy();for(const client of wss?.clients||[])client.terminate();wss?.close();
        server?.closeIdleConnections();server?.closeAllConnections();
        await Promise.allSettled([tcp,server].filter(Boolean).map(value=>new Promise(resolve=>value.close(resolve))));
        await Promise.allSettled(Object.values(files).map(file=>file.close()));
        process.off('SIGINT',signal);process.off('SIGTERM',signal);
    }
    if(error)throw error;
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
