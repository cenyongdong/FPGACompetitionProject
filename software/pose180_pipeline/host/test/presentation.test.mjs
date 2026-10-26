import test from 'node:test';import assert from 'node:assert/strict';
import net from 'node:net';import {spawn} from 'node:child_process';import {once} from 'node:events';
import {fileURLToPath} from 'node:url';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {PresentationReader,decodePresentation,visiblePresentation,VIEW_LIMIT} from '../presentation.mjs';
const frame=(n=1)=>({schema:'PIWVIEW1',version:1,replay:false,session:'18446744073709500000',frame:String(n),sequence:String(n),source_ns:String(1000000000+n*67000000),hold_ms:250,
 poses:[{track:'7',candidate:19,score:.8,held:false,observed_ns:String(1000000000+n*67000000),age_ms:0,joints:Array(42).fill(.3)}],raw_poses:[]});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<150;i++){const v=await fn();if(v)return v;await wait(20);}throw new Error('wait expired');}
async function free(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
test('bounded NDJSON splits/coalescing, finite checks, immutable age and expiry',()=>{
 const r=new PresentationReader(),b=Buffer.from(JSON.stringify(frame())+'\n'+JSON.stringify(frame(2))+'\n'),out=[];
 for(let n=0;n<b.length;n+=17)r.push(b.subarray(n,n+17),f=>out.push(f));assert.equal(out.length,2);
 const f=frame();assert.equal(visiblePresentation(f,250).poses.length,1);assert.equal(visiblePresentation(f,251).poses.length,0);assert.equal(f.poses.length,1);
 assert.throws(()=>new PresentationReader().push(Buffer.alloc(VIEW_LIMIT+1,65),()=>{}));
 for(const mutate of [f=>f.version=2,f=>f.poses[0].age_ms=12,f=>f.poses[0].track='0',f=>f.poses[0].joints[0]=null,f=>f.poses.push(f.poses[0]),f=>f.poses[0].score=Math.fround(.2)]){
  const x=frame();mutate(x);assert.throws(()=>decodePresentation(JSON.stringify(x)));}
});
test('derived TCP has no ACK, expires, rejects malformed records and reconnects',async()=>{
 const sockets=[];let ack=0,child,output='';const source=net.createServer(s=>{sockets.push(s);s.on('data',b=>ack+=b.length);});
 await new Promise(r=>source.listen(0,'127.0.0.1',r));const hp=await free();
 try{child=spawn(process.execPath,[fileURLToPath(new URL('../resident.mjs',import.meta.url)),'--board','127.0.0.1','--port',String(source.address().port),'--http-port',String(hp),'--seconds','5'],{windowsHide:true});const done=once(child,'exit');child.stdout.on('data',b=>output+=b);
  await until(()=>output.includes('RESIDENT_PC_READY')&&sockets.length);const get=async()=>await(await fetch('http://127.0.0.1:'+hp+'/api/state')).json();
  const bytes=Buffer.from(JSON.stringify(frame())+'\n');sockets[0].write(bytes.subarray(0,25));await wait(25);assert.equal((await get()).received,0);sockets[0].write(bytes.subarray(25));await until(async()=> (await get()).received===1);
  await wait(280);assert.equal((await get()).frame.poses.length,0);sockets[0].write('{}\n');await until(()=>sockets.length===2);
  sockets[1].write(JSON.stringify(frame(2))+'\n');const state=await until(async()=>{const x=await get();return x.received===2&&x;});assert.equal(state.invalid,1);assert.equal(ack,0);
  const page=await(await fetch('http://127.0.0.1:'+hp)).text();assert.match(page,/raw-viewport/);assert.match(page,/灰色为暂失/);
  const [code]=await done;assert.equal(code,0);
 }finally{child?.kill();sockets.forEach(s=>s.destroy());await new Promise(r=>source.close(r));}
});
test('historical replay uses local timestamps and makes no board connection',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pose-replay-')),file=path.join(dir,'frames.ndjson');let count=0,child,output='';
 const source=net.createServer(s=>{++count;s.destroy();});await new Promise(r=>source.listen(0,'127.0.0.1',r));
 try{fs.writeFileSync(file,[1,2].map(n=>JSON.stringify({...frame(n),replay:true})).join('\n'));const hp=await free();
  child=spawn(process.execPath,[fileURLToPath(new URL('../resident.mjs',import.meta.url)),'--replay',file,'--board','127.0.0.1','--port',String(source.address().port),'--http-port',String(hp),'--seconds','2'],{windowsHide:true});const done=once(child,'exit');child.stdout.on('data',b=>output+=b);
  await until(()=>output.includes('RESIDENT_PC_READY'));const x=await until(async()=>{const s=await(await fetch('http://127.0.0.1:'+hp+'/api/state')).json();return s.received===2&&s;});assert.equal(x.replay,true);assert.equal(x.frame.replay,true);assert.equal(count,0);assert.equal((await done)[0],0);
 }finally{child?.kill();await new Promise(r=>source.close(r));fs.rmSync(dir,{recursive:true});}
});
