// Optional demo subscriber. No input pacing, archive ACK or board control.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import http from 'node:http';
import {Worker} from 'node:worker_threads';
import {fileURLToPath} from 'node:url';
import {decodeFull,selectTopPoses,FULL_BYTES} from './full_record.mjs';
import {PresentationReader,decodePresentation,visiblePresentation} from './presentation.mjs';

const options=new Map();
for(let i=2;i<process.argv.length;i+=2) {
    if(!process.argv[i+1]||options.has(process.argv[i]))throw new Error('Expected unique --option value');
    options.set(process.argv[i],process.argv[i+1]);
}
const take=(k,f)=>{const v=options.get(k)??f;options.delete(k);return v;};
const mode=take('--mode','view'),replay=take('--replay','');
const board=take('--board','192.168.126.49'),port=Number(take('--port',mode==='view'?'39385':'39383'));
if(!['raw','view'].includes(mode)||replay&&mode!=='view')throw new Error('Invalid presentation mode');
const httpPort=Number(take('--http-port','39380')),output=take('--output','');
const seconds=Number(take('--seconds','0')),mock=take('--mock','0')==='1';
if(options.size||![port,httpPort].every(n=>Number.isInteger(n)&&n>0&&n<=65535)||!Number.isFinite(seconds)||seconds<0)throw new Error('Invalid options');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
let worker,busy=false,pending,recordDrops=0,recorded=0,archiveError='',socket,timer,runtimeTimer,closed=false;
let last=null,lastAt=0,received=0,invalid=0,duplicates=0,reconnects=0,connected=false,used=0;
const recent=[]; // At most 64 reception times, independent of run duration.
const raw=Buffer.alloc(FULL_BYTES);const viewReader=new PresentationReader();let replayTimer,restartReplay;let replayEnded=false;
function accept(next){
 if(last&&next.session===last.session&&BigInt(next.sequence)<=BigInt(last.sequence)){++duplicates;return;}
 last=next;lastAt=performance.now();++received;recent.push(lastAt);if(recent.length>64)recent.shift();
}
if(output&&(replay||mode!=='raw'))throw new Error('Raw archive requires explicit --mode raw without replay');
if(output) {
    fs.mkdirSync(output,{recursive:false});
    worker=new Worker(new URL('./resident_archive.mjs',import.meta.url),{workerData:path.resolve(output)});
    worker.on('message',result=>{busy=false;if(result.ok){++recorded;archiveError='';}else archiveError=result.error;if(pending){const b=pending;pending=undefined;archive(b);}});
    worker.on('error',error=>{archiveError=error.message;pending=undefined;worker=undefined;busy=false;});
}
function archive(bytes) {
    if(!worker)return;
    if(busy){if(pending)++recordDrops;pending=Buffer.from(bytes);return;}
    busy=true;worker.postMessage(Buffer.from(bytes));
}
function connect() {
    if(closed)return;
    used=0;viewReader.reset();socket=net.createConnection({host:board,port});socket.setTimeout(5000);
    socket.setKeepAlive(true,1000);
    // Missing CSI windows do not imply a broken TCP session. The page marks
    // stale results independently; a 30 s idle watchdog still detects dead peers.
    socket.on('connect',()=>{connected=true;++reconnects;socket.setTimeout(30000);});
    socket.on('timeout',()=>socket.destroy());socket.on('error',()=>{});
    socket.on('data',chunk=>{
        if(mode==='view'){try{viewReader.push(chunk,f=>{if(f.replay)throw new Error('Historical record on live channel');accept(f);});}catch{++invalid;socket.destroy();}return;}
        for(let offset=0;offset<chunk.length;) {
            const n=Math.min(FULL_BYTES-used,chunk.length-offset);chunk.copy(raw,used,offset,offset+n);used+=n;offset+=n;
            if(used!==FULL_BYTES)continue;used=0;
            archive(raw);
            try {
                const next=decodeFull(raw);
                next.poses=selectTopPoses(raw,3,0.2);
                if(last && next.session===last.session && BigInt(next.sequence)<=BigInt(last.sequence)){++duplicates;continue;}
                last=next;lastAt=performance.now();++received;
                recent.push(lastAt);if(recent.length>64)recent.shift();
            }
            catch{++invalid;socket.destroy();break;}
        }
    });
    socket.on('close',()=>{connected=false;used=0;if(!closed)timer=setTimeout(connect,1000);});
}
const state=()=>{
    const now=performance.now(),age=last?Math.max(0,Math.floor(now-lastAt)):null;
    const active=recent.filter(t=>now-t<2000);
    const hz=active.length>1?(active.length-1)*1000/(now-active[0]):0;
    const phase=!connected?'reconnecting':!last?'waiting_input':age>=2000?'result_stale':age>=750?'waiting_result':'live';
    return {mock,connected,received,invalid,duplicates,reconnects,recorded,recordDrops,archiveError,
        phase,new_results_hz:Number(hz.toFixed(2)),age_ms:age,mode,replay:!!replay,replayEnded,frame:last?(mode==='view'?visiblePresentation(last,age):last):null};
};
const assets=new Map([['/scene.js',path.join(root,'demo_v1/web/scene.js')],
    ['/vendor/three.module.js',path.join(root,'software/pc_viewer/node_modules/three/build/three.module.js')],
    ['/vendor/three.core.js',path.join(root,'software/pc_viewer/node_modules/three/build/three.core.js')],
    ['/vendor/OrbitControls.js',path.join(root,'software/pc_viewer/node_modules/three/examples/jsm/controls/OrbitControls.js')]]);
const page=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>常驻姿态演示</title>
<style>body{margin:0;background:#0b111b;color:#e5eef9;font:16px system-ui}header{padding:18px 24px 10px}h1{font-size:20px;margin:0 0 12px}#views{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#26384a}#views>section{background:#0b111b}#views h2{font-size:14px;margin:8px 18px;color:#9fc8e7}#viewport,#raw-viewport{height:calc(100vh - 265px);min-height:340px}#views.single{grid-template-columns:1fr}#views.single #raw-panel{display:none}#status{color:#9fc8e7;font-size:14px}#phase{display:inline-block;padding:5px 12px;border-radius:6px;background:#173d36;color:#b3f4db}#phase[data-state]:not([data-state=live]){background:#493d23;color:#ffe0a0}#metrics{color:#c2d6df;font-variant-numeric:tabular-nums;margin:10px 0}small{color:#95a8b9}button{background:#172838;color:#d8e9f6;border:1px solid #385364;border-radius:5px;padding:6px 12px;cursor:pointer}nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}label{font-size:14px;margin-left:8px}#render-rate{margin-left:auto;color:#95a8b9;font-size:13px}</style>
<script type="importmap">{"imports":{"three":"/vendor/three.module.js","three/addons/controls/OrbitControls.js":"/vendor/OrbitControls.js"}}</script>
<header><h1>Wi-Fi 姿态 · PC 观察端</h1><span id="phase" data-state="waiting_input">等待首个真实结果</span><span id="metrics"></span><p id="status">正在连接板端</p><small>拖动旋转 · 滚轮缩放 · 右键平移。人物跟踪与滤波展示，无插帧；暂失姿态有时限，PC 断开不会停止板端。</small>
<nav><button id="replay-again" style="display:${replay?'inline-block':'none'}">重新回放</button><button data-view="perspective">透视</button><button data-view="front">正面</button><button data-view="side">侧面</button><button data-view="top">俯视</button><label><input id="raw-view" type="checkbox" checked>并排原始候选</label><label><input id="labels" type="checkbox">关节编号</label><span id="render-rate">画面绘制 — FPS</span></nav></header><div id="views"><section><h2>后处理 · 稳定人物 ID · 灰色为暂失</h2><div id="viewport"></div></section><section id="raw-panel"><h2>原始 Top3 &gt; 0.2 · 未滤波候选</h2><div id="raw-viewport"></div></section></div>
<script type="module">import {createScene} from './scene.js';
const bones=[[0,1],[0,2],[0,3],[2,4],[2,5],[3,6],[3,7],[4,8],[5,7],[5,9],[6,10],[7,11],[9,12],[11,13]];
const el=id=>document.getElementById(id);let identity='',rawIdentity='',scene,rawScene;const compare=${mode==='view'};
try{scene=createScene(el('viewport'),bones,fps=>{el('render-rate').textContent='画面绘制 '+fps+' FPS（非推理帧率）';},{maxPoses:3});if(compare)rawScene=createScene(el('raw-viewport'),bones,()=>{},{maxPoses:3});else el('views').className='single';}
catch(error){el('phase').textContent='三维渲染不可用';el('phase').dataset.state='error';el('status').textContent='请启用浏览器硬件加速；错误：'+error.message;}
if(scene){
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{scene.view(button.dataset.view);rawScene?.view(button.dataset.view);}));
el('labels').addEventListener('change',event=>{scene.labels(event.target.checked);rawScene?.labels(event.target.checked);});
el('raw-view').addEventListener('change',event=>{el('views').className=compare&&event.target.checked?'':'single';});
el('replay-again').addEventListener('click',()=>fetch('/api/replay/restart',{method:'POST'}));
const phases={live:'真实结果更新中',waiting_input:'等待首个真实结果',waiting_result:'等待新结果',result_stale:'结果已过期',reconnecting:'连接中断 · 自动重连'};
async function update(){try{const response=await fetch('/api/state',{cache:'no-store',signal:AbortSignal.timeout(2000)});if(!response.ok)throw new Error('HTTP '+response.status);const s=await response.json(),f=s.frame;
el('phase').dataset.state=s.phase;el('phase').textContent=(s.replay?'历史回放 · ':s.mock?'模拟测试 · ':'')+(s.replayEnded?'播放结束':phases[s.phase]??'等待新结果');
el('status').textContent=(s.replay?'本地历史记录 · 按原时间戳播放':s.connected?'结果通道已连接':'结果通道重连中')+' · 新结果 '+s.received+' · PC接收后 '+(s.age_ms??'—')+' ms · 新结果 '+s.new_results_hz+' /s · 归档丢弃 '+s.recordDrops+(s.archiveError?' · 归档暂停':'');
el('metrics').textContent=f?'　FRAME '+f.frame+' · TOP 3 · 置信度 > 0.2 · 显示 '+f.poses.length+' 个'+(f.poses.length?' · '+f.poses.map(p=>(p.track?'ID '+p.track+' / ':'')+'SLOT '+p.candidate+' / '+p.score.toFixed(4)+(p.held?' 暂失':'')).join('，'):s.mode==='view'?' · 无可展示轨迹':' · 无合格候选'):'';
if(!f&&compare&&identity){scene.setPose({poses:[]});rawScene?.setPose({poses:[]});identity=rawIdentity='';}if(f){const key=f.session+':'+f.sequence+':'+f.poses.map(p=>p.track??p.candidate).join(',');if(key!==identity){scene.setPose(f);identity=key;}if(rawScene&&f.raw_poses){const rk=f.session+':'+f.sequence+':'+f.raw_poses.length;if(rk!==rawIdentity){rawScene.setPose({...f,poses:f.raw_poses});rawIdentity=rk;}}}}
catch{if(compare){scene.setPose({poses:[]});rawScene?.setPose({poses:[]});identity=rawIdentity='';}el('phase').dataset.state='reconnecting';el('phase').textContent='观察端连接中断';el('status').textContent='等待本机观察服务恢复';}setTimeout(update,100);}update();
window.addEventListener('pagehide',()=>{scene.dispose();rawScene?.dispose();},{once:true});
}</script></html>`;
const server=http.createServer((req,res)=>{
    res.setHeader('Cache-Control','no-store');
    if(replay&&req.method==='POST'&&req.url==='/api/replay/restart'){restartReplay();res.writeHead(204).end();return;}
    if(req.method!=='GET'){res.writeHead(405).end();return;}
    if(req.url==='/api/state'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(state()));return;}
    if(req.url==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(page);return;}
    const file=assets.get(req.url);if(!file){res.writeHead(404).end();return;}
    res.setHeader('Content-Type','text/javascript');fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
});
server.maxConnections=8;server.requestTimeout=5000;
server.listen(httpPort,'127.0.0.1',()=>console.log('RESIDENT_PC_READY',JSON.stringify({url:`http://127.0.0.1:${httpPort}`,board,port,archive:!!output,mock})));
async function stop(){if(closed)return;closed=true;clearTimeout(timer);clearTimeout(runtimeTimer);clearTimeout(replayTimer);socket?.destroy();server.close();server.closeAllConnections();await worker?.terminate();console.log(JSON.stringify(state()));}
process.on('SIGINT',stop);process.on('SIGTERM',stop);
if(replay){
 if(fs.statSync(replay).size>64*1024*1024)throw new Error('Replay exceeds bounded file size');
 const frames=fs.readFileSync(replay,'utf8').trim().split('\n').filter(Boolean).map(decodePresentation);
 if(frames.some(f=>!f.replay))throw new Error('Expected explicitly historical frames');
 let index=0;connected=true;function play(){if(closed||index>=frames.length){replayEnded=true;return;}accept(frames[index]);const current=frames[index++];if(index<frames.length){const next=frames[index];const dt=next.session===current.session?Math.max(0,Number(BigInt(next.source_ns)-BigInt(current.source_ns))/1e6):0;replayTimer=setTimeout(play,dt);}else replayEnded=true;}
 restartReplay=()=>{clearTimeout(replayTimer);last=null;lastAt=0;received=0;recent.length=0;index=0;replayEnded=false;replayTimer=setTimeout(play,250);};restartReplay();
}else connect();if(seconds)runtimeTimer=setTimeout(stop,seconds*1000);
