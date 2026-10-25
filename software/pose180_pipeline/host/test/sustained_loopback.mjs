// Software-only localhost mock. This does not exercise NPU, DDR or HDMI hardware.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { FULL_BYTES,decodeFull } from '../full_record.mjs';
import { BoundedWriter,BufferPool } from '../flow.mjs';
import { record,confirmed } from './fixtures.mjs';

const options={};for(let i=2;i<process.argv.length;i+=2)options[process.argv[i].replace(/^--/,'')]=process.argv[i+1];
const output=path.resolve(options.output||'.local/pose180-pipeline-20261025-r1/localhost-mock-900');
const count=Number(options.count||900),hz=30,creditLimit=8,delayMs=200;
if(!Number.isInteger(count)||count<900||count>54000)throw new Error('Sustained mock requires 900..54000 frames');
await fs.promises.mkdir(output,{recursive:false});
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function bounded(promise,ms,label){let timer;try{return await Promise.race([promise,new Promise((resolve,reject)=>{timer=setTimeout(()=>reject(new Error(label)),ms);})]);}finally{clearTimeout(timer);}}
async function freePort(){const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;await new Promise(resolve=>server.close(resolve));return port;}
async function listenAgain(port){const server=net.createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});await new Promise(resolve=>server.close(resolve));}

const started=process.hrtime.bigint(),queue=[],pool=new BufferPool(creditLimit,86432),sourceStamps=new BigUint64Array(count);
let child=null,inputSocket=null,resultSocket=null,receiveTask=null,stdoutFile=null,stderrFile=null;
let accepted=0,finalSent=0,queueHigh=0,inflightHigh=0,acks=0,mockError=null,wake=null,inputEnded=false;
let ackUsed=0,ackReady=null,ackReject=null,ackWord=Buffer.alloc(8),rawOriginalMatches=0,portsReleased=false;
const ports={input:0,result:await freePort(),http:await freePort()};
const inputServer=net.createServer(socket=>{
    assert.equal(inputSocket,null,'Only one mock input connection');inputSocket=socket;socket.on('error',reason=>{mockError??=reason;wake?.();});
    receiveTask=(async()=>{
        let current=null,used=0;
        for await(const chunk of socket){
            let offset=0;
            while(offset<chunk.length){
                if(!current)current=pool.acquire();
                const take=Math.min(current.length-used,chunk.length-offset);chunk.copy(current,used,offset,offset+take);offset+=take;used+=take;
                if(used!==current.length)continue;
                assert.equal(current.toString('ascii',0,8),'PIWCSI2\0');assert.equal(current.readUInt32LE(8),2);assert.equal(current.readUInt32LE(12),86400);
                assert.equal(current.readBigUInt64LE(16),BigInt(1000000+accepted));assert(accepted<count,'Unexpected extra mock input');
                assert(current.subarray(32).equals(sourcePayload),'Host payload changed in transit/reuse');
                sourceStamps[accepted]=current.readBigUInt64LE(24);++accepted;
                const inflight=accepted-finalSent;assert(inflight<=creditLimit,'Host exceeded global sent-final credit limit');inflightHigh=Math.max(inflightHigh,inflight);
                queue.push({index:accepted-1,bytes:current});queueHigh=Math.max(queueHigh,queue.length);assert(queue.length<=creditLimit);
                current=null;used=0;wake?.();
            }
        }
        assert.equal(used,0,'Truncated mock input');assert.equal(accepted,count);inputEnded=true;wake?.();
    })().catch(reason=>{mockError??=reason;wake?.();throw reason;});
    // Retain the rejection for the coordinated final await, without an unhandled promise.
    receiveTask.catch(()=>{});
});
const sourcePayload=Buffer.alloc(86400);
for(let i=0;i<sourcePayload.length/8;++i)sourcePayload.writeDoubleLE((i%31)/32,i*8);
async function condition(predicate,label){const deadline=Date.now()+5000;while(!predicate()){if(mockError)throw mockError;if(Date.now()>deadline)throw new Error(label);await new Promise(resolve=>{const timer=setTimeout(()=>{wake=null;resolve();},50);wake=()=>{clearTimeout(timer);wake=null;resolve();};});}}
function nextAck(){assert.equal(ackReady,null,'One ACK waiter only');return bounded(new Promise((resolve,reject)=>{ackReady=resolve;ackReject=reject;}),3000,'Host archive ACK timeout');}
let failure=null,summary=null;
try {
    await new Promise(resolve=>inputServer.listen(0,'127.0.0.1',resolve));ports.input=inputServer.address().port;
    fs.mkdirSync(path.join(output,'data'));fs.writeFileSync(path.join(output,'data','aligned.bin'),sourcePayload);
    fs.writeFileSync(path.join(output,'data','catalog.json'),JSON.stringify({mock:true,payload_bytes:86400,sha256:'synthetic-localhost-mock',samples:[{index:0,name:'synthetic-localhost-only'}]}));
    const entry=fileURLToPath(new URL('../run.mjs',import.meta.url)),hostOutput=path.join(output,'host');
    const command=[entry,'--stage','short','--count',String(count),'--hz',String(hz),'--max-inflight',String(creditLimit),'--data',path.join(output,'data'),'--output',hostOutput,'--input-host','127.0.0.1','--input-port',String(ports.input),'--result-port',String(ports.result),'--http-port',String(ports.http),'--linger','0'];
    if(options['pacer-python'])command.push('--pacer-python',options['pacer-python']);
    fs.writeFileSync(path.join(output,'mock-command.json'),JSON.stringify({kind:'software_only_localhost_mock',executable:process.execPath,args:command,count,hz,credit_limit:creditLimit,prefill:creditLimit,injected_final_delay_ms:delayMs,hardware_test:false},null,2)+'\n');
    child=spawn(process.execPath,command,{windowsHide:true,stdio:['ignore','pipe','pipe']});const exited=once(child,'exit');
    stdoutFile=fs.createWriteStream(path.join(output,'host.stdout.log'),{flags:'wx'});stderrFile=fs.createWriteStream(path.join(output,'host.stderr.log'),{flags:'wx'});
    child.stdout.pipe(stdoutFile);child.stderr.pipe(stderrFile);
    let lineTail='',readyResolve;const ready=new Promise(resolve=>{readyResolve=resolve;});
    child.stdout.on('data',chunk=>{lineTail+=chunk.toString();assert(lineTail.length<65536,'Bounded host log parser');let newline;while((newline=lineTail.indexOf('\n'))>=0){const line=lineTail.slice(0,newline);lineTail=lineTail.slice(newline+1);if(line.startsWith('HOST_READY '))readyResolve();}});
    await bounded(ready,10000,'Host mock startup timeout');
    const runtime=JSON.parse(fs.readFileSync(path.join(hostOutput,'runtime.json')));
    resultSocket=net.createConnection(ports.result,'127.0.0.1');resultSocket.setNoDelay(true);resultSocket.on('error',reason=>{mockError??=reason;ackReject?.(reason);});await once(resultSocket,'connect');
    resultSocket.on('data',chunk=>{
        try{let offset=0;while(offset<chunk.length){const take=Math.min(8-ackUsed,chunk.length-offset);chunk.copy(ackWord,ackUsed,offset,offset+take);ackUsed+=take;offset+=take;if(ackUsed===8){assert(ackReady,'Unexpected host ACK');const resolve=ackReady;ackReady=null;ackReject=null;ackUsed=0;resolve(ackWord.readBigUInt64LE());}}}catch(reason){mockError??=reason;ackReject?.(reason);}
    });
    const rawBuffer=Buffer.alloc(FULL_BYTES),finalBuffer=Buffer.alloc(8),writer=new BoundedWriter(resultSocket,FULL_BYTES);
    // Fill precisely the existing eight credits. One 200ms hold after first raw
    // ACK then makes the next absolute send slot expire, without a huge queue.
    await condition(()=>queue.length===creditLimit,'Mock prefill did not reach eight credits');
    for(let index=0;index<count;++index){
        await condition(()=>queue.length>0,'Mock input queue stalled');const item=queue.shift();assert.equal(item.index,index);
        record({index,session:BigInt(runtime.session),source:sourceStamps[index],best:index%180,fullPattern:true,target:rawBuffer});
        const ack=nextAck();
        // Exercise both split headers and split payloads without retaining copies.
        const cut=index%2?19:49157;await writer.write(rawBuffer.subarray(0,cut));await writer.write(rawBuffer.subarray(cut));
        assert.equal(await ack,BigInt(index+1));++acks;
        if(index===0){console.log('MOCK_DELAY_INJECTION',JSON.stringify({after_archive_ack:1,delay_ms:delayMs,prefill:creditLimit}));await wait(delayMs);}
        await writer.write(confirmed(index+1,finalBuffer));++finalSent;pool.release(item.bytes);
        if((index+1)%100===0)console.log('MOCK_PROGRESS',JSON.stringify({received:accepted,confirmed:finalSent,queue:queue.length,inflight_high:inflightHigh,elapsed_s:Number(process.hrtime.bigint()-started)/1e9}));
    }
    resultSocket.end();await condition(()=>inputEnded,'Mock input EOF missing');await receiveTask;
    const [code]=await bounded(exited,10000,'Host did not exit after final mock confirmation');assert.equal(code,0,'Host process failed; inspect preserved logs');
    await Promise.all([stdoutFile,stderrFile].map(stream=>stream.writableFinished?Promise.resolve():once(stream,'finish')));
    const hostSummary=JSON.parse(fs.readFileSync(path.join(hostOutput,'summary.json')));
    assert.equal(hostSummary.all_records_received,true);assert.equal(hostSummary.sent,count);assert.equal(hostSummary.received,count);assert.equal(hostSummary.raw_records,count);assert.equal(hostSummary.unconfirmed_records,0);
    assert.equal(hostSummary.raw_bytes,count*FULL_BYTES);assert.equal(hostSummary.inflight_high,creditLimit);assert.equal(inflightHigh,creditLimit);assert.equal(hostSummary.strict30Hz,false);assert(hostSummary.credit_waits>0);assert(hostSummary.sender_missed_slots>0);
    const sent=fs.readFileSync(path.join(hostOutput,'sent.jsonl'),'utf8').trim().split('\n').map(JSON.parse),received=fs.readFileSync(path.join(hostOutput,'received.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    assert.equal(sent.length,count);assert.equal(received.length,count);
    const recoveryStart=32,recoveryInputRate=(count-recoveryStart-1)*1e9/Number(BigInt(sent.at(-1).source_ns)-BigInt(sent[recoveryStart].source_ns));
    assert(recoveryInputRate>=28.5&&recoveryInputRate<=31,'High-resolution recovery did not sustain approximately 30Hz: '+recoveryInputRate);
    const archive=await fs.promises.open(path.join(hostOutput,'actual.full'),'r'),readBuffer=Buffer.alloc(FULL_BYTES),expected=Buffer.alloc(FULL_BYTES);
    let noCatchupChecks=0,minAfterExpiredSlotMs=Infinity;
    try{
        for(let index=0;index<count;++index){
            const got=await archive.read(readBuffer,0,FULL_BYTES,index*FULL_BYTES);assert.equal(got.bytesRead,FULL_BYTES);
            record({index,session:BigInt(runtime.session),source:sourceStamps[index],best:index%180,fullPattern:true,target:expected});assert(readBuffer.equals(expected),'Complete original bytes mismatch at '+index);++rawOriginalMatches;
            const decoded=decodeFull(readBuffer);assert.equal(decoded.candidate,index%180);assert.equal(received[index].sequence,String(index+1));assert.equal(sent[index].source_ns,sourceStamps[index].toString());assert.equal(decoded.source_ns,sent[index].source_ns);
            assert.equal(BigInt(sent[index].planned_ns),BigInt(sent[0].planned_ns)+BigInt(index)*33333333n,'Absolute epoch rebased');
            if(index&&BigInt(sent[index-1].source_ns)>=BigInt(sent[index].planned_ns)){
                const interval=Number(BigInt(sent[index].source_ns)-BigInt(sent[index-1].source_ns))/1e6;assert(interval>=32.333333,'Catch-up burst after expired slot');minAfterExpiredSlotMs=Math.min(minAfterExpiredSlotMs,interval);++noCatchupChecks;
            }
        }
    }finally{await archive.close();}
    assert(noCatchupChecks>0);assert.equal(acks,count);assert.equal(finalSent,count);assert.equal(pool.owned.size,0);assert.equal(queue.length,0);assert.equal(ackUsed,0);
    summary={kind:'software_only_localhost_mock',hardware_test:false,passed:true,frames:count,requested_hz:hz,elapsed_s:Number(process.hrtime.bigint()-started)/1e9,delay_injection_ms:delayMs,prefill_credits:creditLimit,
        input_bytes_each:86432,result_bytes_each:FULL_BYTES,complete_original_records_matched:rawOriginalMatches,archive_acks:acks,final_confirmations:finalSent,
        max_sent_minus_final:inflightHigh,mock_queue_high:queueHigh,host_strict30Hz:hostSummary.strict30Hz,host_input_rate_hz:hostSummary.input_rate_hz,host_credit_waits:hostSummary.credit_waits,
        recovery_input_rate_hz:recoveryInputRate,recovery_rate_first_invocation:recoveryStart,
        no_catchup_checks:noCatchupChecks,min_interval_after_expired_slot_ms:minAfterExpiredSlotMs,host_exit_code:code,resources_released:false,ports};
}catch(reason){failure=reason;console.error(reason.stack||reason);}finally{
    if(child&&child.exitCode===null){child.kill();await bounded(once(child,'exit'),3000,'Mock host cleanup did not exit').catch(reason=>{failure??=reason;});}
    resultSocket?.destroy();inputSocket?.destroy();await new Promise(resolve=>inputServer.close(resolve));
    await Promise.allSettled([receiveTask].filter(Boolean));
    await Promise.allSettled([stdoutFile,stderrFile].filter(Boolean).map(stream=>stream.writableFinished?Promise.resolve():new Promise(resolve=>stream.end(resolve))));
    try{await Promise.all(Object.values(ports).filter(Boolean).map(listenAgain));portsReleased=true;}catch(reason){failure??=reason;}
    summary??={kind:'software_only_localhost_mock',hardware_test:false,passed:false,frames:count,accepted,archive_acks:acks,final_confirmations:finalSent,complete_original_records_matched:rawOriginalMatches,max_sent_minus_final:inflightHigh,ports};
    summary.resources_released=portsReleased&&(!child||child.exitCode!==null||child.signalCode!==null);if(failure){summary.passed=false;summary.error=String(failure.stack||failure);}
    fs.writeFileSync(path.join(output,'mock-summary.json'),JSON.stringify(summary,null,2)+'\n');console.log('MOCK_COMPLETE',JSON.stringify(summary));
}
if(failure)process.exitCode=1;
