import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
import { once } from 'node:events';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import os from 'node:os';
import { ConfirmedStream,decodeFull,FULL_BYTES } from './full_record.mjs';
import { BONES } from './protocol.mjs';
import {HostDeliveryTiming,archiveRecord} from './delivery_timing.mjs';

const HERE=path.dirname(fileURLToPath(import.meta.url)), ROOT=path.resolve(HERE,'../..');
const options={}; for(let i=2;i<process.argv.length;i+=2) options[process.argv[i].replace(/^--/,'')]=process.argv[i+1];
const stage=options.stage || 'basic', counts={basic:3,short:900,medium:9000,stress:54000};
const count=options.frames?Number(options.frames):counts[stage], hz=stage==='basic'?5:30;
if(!Number.isInteger(count)||count<1||count>54000)throw new Error('Invalid frame bound');
if(!count) throw new Error('Unknown stage');
const data=path.resolve(options.data || path.join(ROOT,'demo_v1/data/full'));
const output=path.resolve(options.output || path.join(ROOT,'demo_v1/runs',stage));
fs.mkdirSync(output,{recursive:false});
const catalog=JSON.parse(fs.readFileSync(path.join(data,'catalog.json')));
const sourceSpecs=catalog.sources||{test:{path:path.join(data,'aligned.bin'),count:catalog.samples.length}};
const payloadFiles={};
for(const [split,spec]of Object.entries(sourceSpecs)) {
    const file=await fs.promises.open(spec.path,'r');
    if((await file.stat()).size!==spec.count*86400)throw new Error('Incomplete aligned source: '+split);
    payloadFiles[split]=file;
}
if(!catalog.samples.length)throw new Error('Empty dataset');
const dependency=path.join(ROOT,'software/pc_viewer/node_modules');
const {WebSocketServer,WebSocket}=createRequire(import.meta.url)(path.join(dependency,'ws'));
const session=BigInt(Date.now()), stamps=[], errors=[], latencies=[], processes=[], arrivals=[], queues=[], lateness=[];
const splitCounts={test:0,train:0};
const clock=()=>process.hrtime.bigint();
const delivery=new HostDeliveryTiming(count,clock);
const delayMs=Number(options['archive-delay-ms']||0),delayEvery=Number(options['archive-delay-every']||300);
if(!Number.isFinite(delayMs)||delayMs<0||delayMs>500||!Number.isInteger(delayEvery)||delayEvery<1||delayMs&&stage!=='short')throw new Error('Invalid short-test archive delay');
// 仅提高本进程的调度优先级；退出即回收，不改变系统电源/定时器设置。
try{os.setPriority(0,os.constants.priority.PRIORITY_ABOVE_NORMAL);}catch(e){console.warn('Process priority unchanged:',e.message);}
// 在计时前预分配，避免逐帧扩展文件的NTFS元数据停顿。
const rawPath=path.join(output,'actual.full'),rawFd=fs.openSync(rawPath,'wx');
fs.ftruncateSync(rawFd,count*FULL_BYTES);
const raw=fs.createWriteStream(rawPath,{fd:rawFd,autoClose:false,start:0});
const metadata=fs.createWriteStream(path.join(output,'received.jsonl'));
const sends=fs.createWriteStream(path.join(output,'sent.jsonl'));
let received=0,sent=0,complete=false,closing=false,connection=null,input=null,last=null,sending=false,expectedEnd=false;
let sendStart=null,sendEnd=null,receiveStart=null,receiveEnd=null;
let pacer=null;
const pendingSaves=new Set();
const wss=new WebSocketServer({noServer:true,perMessageDeflate:false,maxPayload:1024});
const status=()=>({stage,session:session.toString(),target:count,hz,sent,received,complete,errors,
    last_frame:last?.frame,received_hz:arrivals.length>1 ? (arrivals.length-1)*1e9/Number(arrivals.at(-1)-arrivals[0]):0,
    last_latency_ms:latencies.at(-1)??null,last_process_ms:processes.at(-1)??null,connected:!!connection,
    model:'shared FP16 · ZG330 / PS',bones:BONES,HDMI:false});
const broadcast=data=>{const encoded=JSON.stringify(data);for(const ws of wss.clients) if(ws.readyState===WebSocket.OPEN) {if(ws.bufferedAmount>65536)ws.terminate();else ws.send(encoded);}};
function fail(error) {
    if(closing)return;
    errors.push(String(error.message||error)); console.error('HOST_STOP',String(error.message||error));pacer?.kill();
    broadcast({type:'status',status:status()}); input?.destroy(); connection?.destroy(); process.exitCode=1;
    finish(false).catch(e=>console.error(e));
}
for(const stream of [raw,metadata,sends])stream.on('error',fail);
const files=new Map([['/','index.html'],['/app.js','app.js'],['/scene.js','scene.js'],['/style.css','style.css']]);
const vendors=new Map([['/vendor/three.module.js','three/build/three.module.js'],['/vendor/three.core.js','three/build/three.core.js'],['/vendor/OrbitControls.js','three/examples/jsm/controls/OrbitControls.js']]);
const server=http.createServer((req,res)=> {
    if(req.method!=='GET'){res.writeHead(405).end();return;}
    if(req.url==='/api/status'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(status()));return;}
    if(req.url==='/favicon.ico'){res.writeHead(204).end();return;}
    const name=files.get(req.url),vendor=vendors.get(req.url);
    if(!name&&!vendor){res.writeHead(404).end();return;}
    res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type',req.url.endsWith('.js')?'text/javascript':req.url.endsWith('.css')?'text/css':'text/html; charset=utf-8');
    fs.createReadStream(vendor?path.join(dependency,vendor):path.join(HERE,'../web',name)).on('error',e=>res.destroy(e)).pipe(res);
});
server.on('upgrade',(req,socket,head)=> {
    if(req.url!=='/updates'||(req.headers.origin&&req.headers.origin!=='http://127.0.0.1:39380')){socket.destroy();return;}
    wss.handleUpgrade(req,socket,head,ws=>{wss.emit('connection',ws,req);ws.send(JSON.stringify({type:'status',status:status()}));if(last)ws.send(JSON.stringify({type:'frame',frame:last}));});
});
const tcp=net.createServer(socket=> {
    if(connection||complete||closing){socket.destroy();return;}
    connection=socket;socket.setNoDelay(true);socket.setTimeout(60000,()=>fail(new Error('Result input stalled for 60s')));
    const parser=new ConfirmedStream();let pending=null,rawCount=0;
    socket.on('data',chunk=> {
        try {
            for(const row of parser.push(chunk)) {
                if(row.type==='raw') {
                    const ordinal=rawCount++;delivery.mark(ordinal,'raw_ready');
                    // 先保存全部字节。写入回调完成后才校验并发送回执。
                    const delayed=delayMs&&ordinal>0&&ordinal%delayEvery===0?delayMs:0;
                    delivery.mark(ordinal,'save_begin');
                    const saving=archiveRecord(raw,row.raw,delayed,error=>{
                        delivery.mark(ordinal,'save_end');
                        if(error){fail(error);return;}
                        if(closing)return;
                        try {
                            const f=decodeFull(row.raw);
                            delivery.mark(ordinal,'decode_end');
                            if(pending||received>=count||f.session!==session.toString()||f.frame!==String(1000000+received)||f.invocation!==String(received)||f.sequence!==String(received+1)||f.source_ns!==stamps[received]?.toString())throw new Error('Input/result identity or sequence mismatch');
                            pending=f;const ack=Buffer.alloc(8);ack.writeBigUInt64LE(BigInt(f.sequence));
                            delivery.mark(ordinal,'ack_queued');
                            socket.write(ack,error=>{if(error){fail(error);return;}delivery.mark(ordinal,'ack_flushed');});
                        }catch(e){fail(e);}
                    });
                    pendingSaves.add(saving);saving.finally(()=>pendingSaves.delete(saving));
                    continue;
                }
                if(!pending||BigInt(pending.sequence)!==row.sequence)throw new Error('Board numeric confirmation differs');
                const f=pending,now=clock();pending=null;
                delivery.mark(received,'confirmation');
                const elapsed=Number(now-BigInt(f.source_ns))/1e6;
                const sample=catalog.samples[received%catalog.samples.length];
                f.sample=sample.name;f.split=sample.split||'test';f.end_to_end_ms=elapsed;++splitCounts[f.split];
                metadata.write(JSON.stringify({frame:f.frame,invocation:f.invocation,sample:f.sample,split:f.split,pc_received_ns:now.toString(),end_to_end_ms:elapsed,...f.metrics})+'\n');
                latencies.push(elapsed);processes.push(f.metrics.process_ms);queues.push(f.metrics.queue_ms);arrivals.push(now);
                if(receiveStart===null)receiveStart=now;receiveEnd=now;++received;last=f;
                broadcast({type:'frame',frame:f});
            }
        }catch(e){fail(e);}
    });
    socket.on('error',fail);
    socket.on('end',()=> {
        try {parser.finish();if(received!==count||sent!==count)throw new Error('Incomplete live run at result EOF');expectedEnd=true;finish(true).catch(fail);}catch(e){fail(e);}
    });
    socket.on('close',()=>{connection=null;if(!expectedEnd&&!closing)fail(new Error('Result stream closed unexpectedly'));});
    if(!sending){sending=true;sendInputs().catch(fail);}
});
async function connectInput() {
    const deadline=Date.now()+30000;
    while(Date.now()<deadline&&!closing){
        const socket=new net.Socket();
        try {await new Promise((resolve,reject)=>{socket.once('error',reject);socket.connect(39382,'192.168.126.49',resolve);});socket.removeAllListeners('error');return socket;}
        catch(e){socket.destroy();if(!['ECONNREFUSED','ETIMEDOUT'].includes(e.code))throw e;await new Promise(r=>setTimeout(r,100));}
    }
    throw new Error('Board input listener startup timeout');
}
async function sendInputs() {
    input=await connectInput();input.setNoDelay(true);input.on('error',fail);
    const cache=new Map();
    async function readPayload(i) {
        const sample=catalog.samples[i%catalog.samples.length],file=payloadFiles[sample.split||'test'];
        const buffer=Buffer.allocUnsafe(86400);let offset=0;
        while(offset<buffer.length){const n=await file.read(buffer,offset,buffer.length-offset,(sample.payload_index??sample.index)*86400+offset);if(!n.bytesRead)throw new Error('Truncated CSI source');offset+=n.bytesRead;}
        return buffer;
    }
    function prefetch(i){if(i<count)cache.set(i,readPayload(i).catch(e=>{fail(e);return null;}));}
    const lookahead=128;
    for(let i=0;i<Math.min(count,lookahead);++i)prefetch(i);
    await Promise.all(cache.values());
    pacer=spawn(options['pacer-python']||'python',[path.join(HERE,'pacer.py'),String(count),String(hz)],{windowsHide:true,stdio:['ignore','pipe','pipe']});
    try{os.setPriority(pacer.pid,os.constants.priority.PRIORITY_ABOVE_NORMAL);}catch{}
    pacer.on('error',fail);pacer.stderr.on('data',data=>fail(new Error('Pacer: '+data.toString())));
    let epoch=null,i=0;
    for await(const line of createInterface({input:pacer.stdout})) {
        if(closing)break;
        if(Number(line)!==i||i>=count)throw new Error('Pacing tick sequence differs');
        const tickReceived=clock();
        const payload=await cache.get(i);cache.delete(i);prefetch(i+lookahead);
        if(!payload)throw new Error('CSI prefetch failed');
        const stamp=clock();if(epoch===null){epoch=stamp;sendStart=stamp;}
        const planned=epoch+BigInt(Math.round(i*1e9/hz));
        const late=Number(stamp-planned)/1e6;stamps.push(stamp);lateness.push(late);
        if(late>20)throw new Error('Host missed absolute send slot by '+late.toFixed(3)+'ms; no catch-up burst');
        const header=Buffer.alloc(32);header.write('PIWCSI2\0',0,'ascii');header.writeUInt32LE(2,8);header.writeUInt32LE(86400,12);
        header.writeBigUInt64LE(BigInt(1000000+i),16);header.writeBigUInt64LE(stamp,24);
        const source=i%catalog.samples.length;
        const record=Buffer.concat([header,payload]);
        const writable=input.write(record);++sent;sendEnd=clock();
        if(!sends.write(JSON.stringify({frame:1000000+i,sample:catalog.samples[source].name,split:catalog.samples[source].split||'test',planned_ns:planned.toString(),source_ns:stamp.toString(),send_end_ns:sendEnd.toString(),late_ms:late,prefetch_wait_ms:Number(stamp-tickReceived)/1e6})+'\n'))await once(sends,'drain');
        if(!writable)await once(input,'drain');
        ++i;
    }
    if(!closing&&i!==count)throw new Error('Pacer ended before final input');
    if(!closing)input.end();
}
function stats(values) {
    if(!values.length)return null;
    const sorted=[...values].sort((a,b)=>a-b);
    return {mean:values.reduce((a,b)=>a+b,0)/values.length,p95:sorted[Math.ceil(values.length*.95)-1],p99:sorted[Math.ceil(values.length*.99)-1],max:sorted.at(-1),over_33_333_ms:values.filter(x=>x>1000/30).length};
}
async function finish(success) {
    if(closing)return;closing=true;complete=success;clearInterval(heartbeat);
    await Promise.allSettled([...pendingSaves]);
    await Promise.all([raw,metadata,sends].map(stream=>new Promise(resolve=>stream.end(resolve))));
    fs.ftruncateSync(rawFd,raw.bytesWritten);fs.closeSync(rawFd);
    delivery.save(output);
    const intervals=arrivals.slice(1).map((t,i)=>Number(t-arrivals[i])/1e6);
    const report={...status(),unique_source_count:Math.min(received,catalog.samples.length),split_counts:splitCounts,dataset_sha256:catalog.sha256,
        input_rate_hz:sent>1?(sent-1)*1e9/Number(stamps.at(-1)-stamps[0]):0,
        output_rate_hz:received>1?(received-1)*1e9/Number(receiveEnd-receiveStart):0,
        process_ms:stats(processes),end_to_end_ms:stats(latencies),output_interval_ms:stats(intervals),queue_ms:stats(queues),sender_late_ms:stats(lateness),
        raw_bytes:fs.statSync(path.join(output,'actual.full')).size,
        archive_delay_injection_ms:delayMs,archive_delay_every:delayEvery,
        all_records_received:success&&received===count,
        strict_33_333ms_processing_pass:success&&processes.every(x=>x<=1000/30),
        strict_33_333ms_end_to_end_pass:success&&latencies.every(x=>x<=1000/30)};
    fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(report,null,2)+'\n');
    console.log('HOST_COMPLETE',JSON.stringify(report));broadcast({type:'status',status:status()});
    setTimeout(shutdown,Number(options.linger||60)*1000);
}
function shutdown(){pacer?.kill();input?.destroy();connection?.destroy();for(const ws of wss.clients)ws.terminate();wss.close();tcp.close();server.close();for(const file of Object.values(payloadFiles))file.close().catch(()=>{});}
process.on('SIGINT',()=>{if(!closing)fail(new Error('User cancelled host run'));shutdown();});
server.on('error',fail);tcp.on('error',fail);
const heartbeat=setInterval(()=>broadcast({type:'status',status:status()}),1000);
await new Promise(resolve=>tcp.listen(39381,'127.0.0.1',resolve));
await new Promise(resolve=>server.listen(39380,'127.0.0.1',resolve));
fs.writeFileSync(path.join(output,'runtime.json'),JSON.stringify({pid:process.pid,session:session.toString(),stage,count,hz,output,data,dataset_sha256:catalog.sha256}));
console.log('HOST_READY',JSON.stringify({session:session.toString(),stage,count,hz,url:'http://127.0.0.1:39380'}));
