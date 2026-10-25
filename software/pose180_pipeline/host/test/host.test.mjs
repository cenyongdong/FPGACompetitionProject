import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { Writable } from 'node:stream';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { FULL_BYTES,SCORE_OFFSET,POSE_OFFSET,decodeFull,ConfirmedReader } from '../full_record.mjs';
import { CreditWindow,BoundedWriter,BufferPool,SendSchedule } from '../flow.mjs';
import { record,confirmed } from './fixtures.mjs';
import { main } from '../run.mjs';

const wait = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function bounded(promise,ms,label){let timer;try{return await Promise.race([promise,new Promise((resolve,reject)=>{timer=setTimeout(()=>reject(new Error(label)),ms);})]);}finally{clearTimeout(timer);}}
async function until(predicate,label){const deadline=Date.now()+5000;while(!predicate()){if(Date.now()>deadline)throw new Error(label);await wait(1);}}

test('PIWFUL3 accepts query179 and rejects wrong length/count, illegal selection and non-finite values',()=>{
    assert.equal(decodeFull(record()).candidate,179);
    assert.throws(()=>decodeFull(record().subarray(0,FULL_BYTES-1)),/record/);
    const badCount=record();badCount.writeUInt32LE(100,116);assert.throws(()=>decodeFull(badCount),/candidate count/);
    const badCandidate=record();badCandidate.writeUInt32LE(180,128+56);assert.throws(()=>decodeFull(badCandidate),/candidate/);
    for(const offset of [384,SCORE_OFFSET,POSE_OFFSET]){const bad=record();bad.writeFloatLE(NaN,offset);assert.throws(()=>decodeFull(bad),/Non-finite/);}
});

test('fixed confirmed reader survives arbitrary split/coalescing and awaits raw ownership',async()=>{
    const rows=[record(),record({index:1})],wire=Buffer.concat([rows[0],confirmed(1),rows[1],confirmed(2)]),reader=new ConfirmedReader();
    const events=[],rawIdentities=[];let offset=0,step=1;
    while(offset<wire.length){const size=Math.min((step*7919)%65537+1,wire.length-offset);await reader.push(wire.subarray(offset,offset+size),async raw=>{rawIdentities.push(raw);await wait(1);events.push(['raw',decodeFull(raw).sequence]);},async sequence=>events.push(['confirmed',sequence.toString()]));offset+=size;++step;}
    reader.finish();assert.deepEqual(events,[['raw','1'],['confirmed','1'],['raw','2'],['confirmed','2']]);assert.equal(rawIdentities[0],rawIdentities[1]);
    for(const cut of [1,7,FULL_BYTES-1,FULL_BYTES,FULL_BYTES+1,FULL_BYTES+7]){const partial=new ConfirmedReader();await partial.push(wire.subarray(0,cut),async()=>{},async()=>{});assert.throws(()=>partial.finish(),/Truncated/);assert.equal(partial.partial().length,cut<FULL_BYTES?cut:cut-FULL_BYTES);}
});

test('invalid/non-finite original record is saved completely before decode, and is never ACKed',async()=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pose180-raw-'));
    try{
        const bytes=record();bytes.writeFloatLE(NaN,POSE_OFFSET+16);
        const filename=path.join(temp,'actual.full'),stream=fs.createWriteStream(filename),writer=new BoundedWriter(stream,FULL_BYTES),reader=new ConfirmedReader();let acked=false;
        await assert.rejects(reader.push(bytes,async raw=>{await writer.write(raw);decodeFull(raw);acked=true;},async()=>{}),/Non-finite/);
        await writer.end();assert.deepEqual(fs.readFileSync(filename),bytes);assert.equal(acked,false);assert.equal(reader.pending,true);assert.throws(()=>reader.finish(),/unconfirmed/);
    }finally{fs.rmSync(temp,{recursive:true,force:true});}
});

test('credit bound resumes only on final confirmation, ages out, and wakes on closure',async()=>{
    let now=1n;const credit=new CreditWindow(2,30,()=>now);credit.reserve(0,now);credit.reserve(1,now);assert.equal(credit.high,2);assert.throws(()=>credit.reserve(2,now),/bound/);
    let woke=false;const waiting=credit.wait().then(()=>{woke=true;});await wait(5);assert.equal(woke,false);credit.confirm(0);await waiting;credit.reserve(2,now);assert.equal(credit.pending.size,2);
    now=31000002n;assert.throws(()=>credit.checkAge(),/age budget/);await assert.rejects(credit.wait(),/age budget/);
    const closed=new CreditWindow(1,1000);closed.reserve(0,process.hrtime.bigint());const blocked=closed.wait();closed.close(new Error('cancelled'));await assert.rejects(blocked,/cancelled/);
    assert.throws(()=>new CreditWindow(65,1000),/bound/);
});

test('bounded callback/drain writer retains fixed buffers and rejects overlapping writes',async()=>{
    let callback,seen;
    const sink=new Writable({highWaterMark:1,write(bytes,encoding,done){seen=bytes;callback=done;}}),writer=new BoundedWriter(sink,16),pool=new BufferPool(1,16),slot=pool.acquire();slot.fill(17);
    let finished=false;const writing=writer.write(slot).then(()=>{pool.release(slot);finished=true;});await wait(2);
    assert.equal(writer.busy,true);assert.equal(writer.bytes,16);assert.equal(finished,false);assert.throws(()=>pool.acquire(),/exhausted/);await assert.rejects(writer.write(Buffer.alloc(1)),/bound/);assert.equal(seen[0],17);
    callback();await writing;const next=pool.acquire();assert.equal(next,slot);next.fill(23);pool.release(next);await writer.end();assert.equal(writer.high,16);
    const broken=new Writable({write(bytes,encoding,done){setImmediate(()=>done(new Error('disk failed')));}});await assert.rejects(new BoundedWriter(broken,10).write(Buffer.alloc(4)),/disk failed/);
});

test('absolute sender slots never rebase after credit pause and prohibit catch-up',()=>{
    const schedule=new SendSchedule(30,10);schedule.epoch=1000000000n;schedule.mark(0,1000000000n);schedule.mark(1,1100000000n);
    assert.equal(schedule.strict,false);assert.equal(schedule.planned(2),1066666666n);assert.equal(schedule.earliest(2),1133333333n);assert.throws(()=>schedule.mark(2,1101000000n),/Catch-up/);
    const normal=new SendSchedule(30);normal.epoch=1000000000n;normal.mark(0,1002000000n);assert.equal(normal.earliest(1),normal.planned(1));normal.mark(1,1035333333n);assert.equal(normal.strict,true);
});

async function freePort(){const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;await new Promise(resolve=>server.close(resolve));return port;}

test('cancelling before first result connection rejects the admission wait and frees ports',async()=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pose180-startup-cancel-')),resultPort=await freePort(),httpPort=await freePort();
    try{
        fs.mkdirSync(path.join(temp,'data'));fs.writeFileSync(path.join(temp,'data','aligned.bin'),Buffer.alloc(86400));
        fs.writeFileSync(path.join(temp,'data','catalog.json'),JSON.stringify({payload_bytes:86400,sha256:'mock',samples:[{index:0,name:'startup-cancel-mock'}]}));
        const running=main(['--stage','basic','--count','1','--data',path.join(temp,'data'),'--output',path.join(temp,'out'),'--input-host','127.0.0.1','--result-port',String(resultPort),'--http-port',String(httpPort),'--linger','0']);
        // Install rejection handling before emitting the same signal path used by CLI.
        const rejection=assert.rejects(running,/User cancelled host run/);
        await until(()=>fs.existsSync(path.join(temp,'out','runtime.json')),'Admission startup timeout');process.emit('SIGINT');
        await bounded(rejection,2000,'Cancelled admission promise stayed pending');
        for(const port of [resultPort,httpPort]){const server=net.createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});await new Promise(resolve=>server.close(resolve));}
        const summary=JSON.parse(fs.readFileSync(path.join(temp,'out','summary.json')));assert.equal(summary.complete,false);assert.equal(summary.sent,0);
    }finally{fs.rmSync(temp,{recursive:true,force:true});}
});

test('host mock run archives full 180 results, returns credits, and flags stalled 30Hz schedule',async()=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pose180-host-')),count=5;
    let child,resultSocket,inputSocket;
    const inputServer=net.createServer(socket=>{inputSocket=socket;});
    await new Promise(resolve=>inputServer.listen(0,'127.0.0.1',resolve));const inputPort=inputServer.address().port;
    const resultPort=await freePort(),httpPort=await freePort();
    try{
        fs.mkdirSync(path.join(temp,'data'));fs.writeFileSync(path.join(temp,'data','aligned.bin'),Buffer.alloc(86400));
        fs.writeFileSync(path.join(temp,'data','catalog.json'),JSON.stringify({payload_bytes:86400,sha256:'mock',samples:[{index:0,name:'mock'}]}));
        const entry=fileURLToPath(new URL('../run.mjs',import.meta.url));
        child=spawn(process.execPath,[entry,'--stage','short','--count',String(count),'--hz','30','--max-inflight','2','--data',path.join(temp,'data'),'--output',path.join(temp,'out'),'--input-host','127.0.0.1','--input-port',String(inputPort),'--result-port',String(resultPort),'--http-port',String(httpPort),'--linger','0'],{windowsHide:true,stdio:['ignore','pipe','pipe']});
        const exit=once(child,'exit');let stdout='',stderr='';child.stderr.on('data',b=>{stderr+=b;});
        await bounded(new Promise((resolve,reject)=>{child.stdout.on('data',b=>{stdout+=b;if(stdout.includes('HOST_READY '))resolve();});child.once('error',reject);}),10000,'Host ready timeout');
        const runtime=JSON.parse(fs.readFileSync(path.join(temp,'out','runtime.json')));
        resultSocket=net.createConnection(resultPort,'127.0.0.1');await once(resultSocket,'connect');
        await until(()=>!!inputSocket,'Mock input connection timeout');
        const frames=[];let tail=Buffer.alloc(0);inputSocket.on('data',chunk=>{tail=Buffer.concat([tail,chunk]);while(tail.length>=86432){frames.push(Buffer.from(tail.subarray(0,86432)));tail=tail.subarray(86432);}});
        let ackTail=Buffer.alloc(0);const ackQueue=[];resultSocket.on('data',chunk=>{ackTail=Buffer.concat([ackTail,chunk]);while(ackTail.length>=8){ackQueue.push(ackTail.readBigUInt64LE());ackTail=ackTail.subarray(8);}});
        for(let index=0;index<count;++index){
            await until(()=>frames.length>index,'Mock input record timeout: '+index);
            if(index===0)await wait(150); // exhaust two credits; schedule must stay visibly late.
            const source=frames[index].readBigUInt64LE(24),bytes=record({index,session:BigInt(runtime.session),source});
            resultSocket.write(bytes.subarray(0,19));resultSocket.write(bytes.subarray(19));
            await until(()=>ackQueue.length>index,'Archive ACK timeout: '+index);assert.equal(ackQueue[index],BigInt(index+1));resultSocket.write(confirmed(index+1));
        }
        resultSocket.end();
        const [code]=await bounded(exit,10000,'Host exit timeout: '+stderr);
        assert.equal(code,0,stderr);const summary=JSON.parse(fs.readFileSync(path.join(temp,'out','summary.json')));
        assert.equal(summary.received,count);assert.equal(summary.raw_bytes,count*FULL_BYTES);assert.equal(summary.inflight_high,2);assert.equal(summary.strict30Hz,false);assert(summary.sender_missed_slots>0);assert(summary.credit_waits>0);assert.equal(summary.all_records_received,true);
        assert.equal(fs.readFileSync(path.join(temp,'out','received.jsonl'),'utf8').trim().split('\n').length,count);
        const archive=fs.readFileSync(path.join(temp,'out','actual.full'));for(let index=0;index<count;++index)assert.equal(decodeFull(archive.subarray(index*FULL_BYTES,(index+1)*FULL_BYTES)).candidate,179);
    }finally{child?.kill();resultSocket?.destroy();inputSocket?.destroy();await new Promise(resolve=>inputServer.close(resolve));fs.rmSync(temp,{recursive:true,force:true});}
});
