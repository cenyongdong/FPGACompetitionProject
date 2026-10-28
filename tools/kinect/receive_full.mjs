// Passive result subscriber: never starts the board, routers, SDK, or training.
import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {FULL_BYTES,decodeFull} from '../../software/pose180_pipeline/host/full_record.mjs';

export async function receive({host,output,seconds=60,port=39383,simulation=false}) {
    const octets=host.split('.').map(Number);
    const privateHost=octets.length===4&&octets.every(x=>Number.isInteger(x)&&x>=0&&x<=255)&&
        (octets[0]===10||(octets[0]===192&&octets[1]===168)||(octets[0]===172&&octets[1]>=16&&octets[1]<=31));
    if(!(privateHost||(simulation&&host==='127.0.0.1'))||!(seconds>=1&&seconds<=600)||!(port>=1024&&port<=65535))
        throw Error('Explicit owned private host, port, and 1..600 second budget required');
    fs.mkdirSync(output); // refuses existing captures
    const raw=fs.openSync(path.join(output,'actual.full'),'wx');
    const ledger=fs.openSync(path.join(output,'arrival.jsonl'),'wx');
    const partial=Buffer.alloc(FULL_BYTES);
    let used=0,records=0,invalid=0,reason='EOF',error=null,previous=null,identityChanges=0,connected=false;
    const start=Date.now();
    fs.writeFileSync(path.join(output,'metadata.json'),JSON.stringify({schema:'KINECT-CSI-TAP1',host,port,seconds,simulation,
        starts_board:false,starts_routers:false,starts_training:false,input:'actual board preprocessing tensor at byte384, float32[180,60]',
        label_source:'Kinect only; model predicted poses are never training labels',
        receipt_clock:'PC UTC and Node monotonic receipt time; neither is RF capture time',
        synchronization_verified:false})+'\n',{flag:'wx'});
    const socket=net.createConnection({host,port});
    const finished=new Promise(resolve=>{
        socket.on('connect',()=>{connected=true;console.log('Connected passive PIWFUL3 subscriber');});
        socket.on('data',chunk=>{
            const arrivalUtc=new Date().toISOString(),receiptNs=process.hrtime.bigint().toString();
            try {
                let offset=0;
                while(offset<chunk.length){
                    const count=Math.min(FULL_BYTES-used,chunk.length-offset);
                    chunk.copy(partial,used,offset,offset+count);used+=count;offset+=count;
                    if(used!==FULL_BYTES)continue;
                    // Preserve the entire original record before validation.
                    fs.writeSync(raw,partial);used=0;
                    let row={record:records++,host_received_utc:arrivalUtc,host_received_monotonic_ns:receiptNs};
                    try {
                        const decoded=decodeFull(partial);
                        row={...row,valid:true,session:decoded.session,frame:decoded.frame,invocation:decoded.invocation,
                            sequence:decoded.sequence,source_ns:decoded.source_ns};
                        if(previous&&(previous.session!==row.session||BigInt(row.sequence)<=BigInt(previous.sequence)))++identityChanges;
                        previous=row;
                    } catch(e){++invalid;row={...row,valid:false,error:String(e)};}
                    fs.writeSync(ledger,JSON.stringify(row)+'\n');
                }
            }catch(e){error=String(e);reason='local_write_error';socket.destroy();}
        });
        socket.on('error',e=>{error=String(e);reason='socket_error';});
        socket.on('close',resolve);
    });
    const timer=setTimeout(()=>{reason='finite_budget';socket.destroy();},seconds*1000);
    const stop=()=>{reason='cancelled';socket.destroy();};process.once('SIGINT',stop);process.once('SIGTERM',stop);
    try {await finished;} finally {
        clearTimeout(timer);process.removeListener('SIGINT',stop);process.removeListener('SIGTERM',stop);
        if(used)fs.writeFileSync(path.join(output,'trailing-partial.bin'),partial.subarray(0,used),{flag:'wx'});
        fs.closeSync(raw);fs.closeSync(ledger);
    }
    const report={connected,records,invalid,identity_changes_or_reordered_records:identityChanges,trailing_bytes:used,
        elapsed_seconds:(Date.now()-start)/1000,reason,error,simulation,socket_closed:socket.destroyed};
    fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
    return report;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
    const [host,output,duration,port]=process.argv.slice(2);
    if(!host||!output||!duration)throw Error('Usage: node receive_full.mjs HOST NEW_OUTPUT SECONDS [PORT]');
    const result=await receive({host,output,seconds:Number(duration),port:port?Number(port):39383});
    console.log(JSON.stringify(result));if(result.error||!result.records)process.exitCode=1;
}
