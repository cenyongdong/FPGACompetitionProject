// Optional demo subscriber. No input pacing, archive ACK or board control.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import http from 'node:http';
import {Worker} from 'node:worker_threads';
import {fileURLToPath} from 'node:url';
import {decodeFull,FULL_BYTES} from './full_record.mjs';

const options=new Map();
for(let i=2;i<process.argv.length;i+=2) {
    if(!process.argv[i+1]||options.has(process.argv[i]))throw new Error('Expected unique --option value');
    options.set(process.argv[i],process.argv[i+1]);
}
const take=(k,f)=>{const v=options.get(k)??f;options.delete(k);return v;};
const board=take('--board','192.168.126.49'),port=Number(take('--port','39383'));
const httpPort=Number(take('--http-port','39380')),output=take('--output','');
const seconds=Number(take('--seconds','0')),mock=take('--mock','0')==='1';
if(options.size||![port,httpPort].every(n=>Number.isInteger(n)&&n>0&&n<=65535))throw new Error('Invalid options');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
let worker,busy=false,pending,recordDrops=0,recorded=0,archiveError='',socket,timer,closed=false;
let last=null,lastAt=0,received=0,invalid=0,reconnects=0,connected=false,used=0;
const raw=Buffer.alloc(FULL_BYTES);
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
    used=0;socket=net.createConnection({host:board,port});socket.setTimeout(5000);
    socket.on('connect',()=>{connected=true;++reconnects;});
    socket.on('timeout',()=>socket.destroy());socket.on('error',()=>{});
    socket.on('data',chunk=>{
        for(let offset=0;offset<chunk.length;) {
            const n=Math.min(FULL_BYTES-used,chunk.length-offset);chunk.copy(raw,used,offset,offset+n);used+=n;offset+=n;
            if(used!==FULL_BYTES)continue;used=0;
            archive(raw);
            try {last=decodeFull(raw);lastAt=Date.now();++received;}
            catch{++invalid;socket.destroy();break;}
        }
    });
    socket.on('close',()=>{connected=false;used=0;if(!closed)timer=setTimeout(connect,1000);});
}
const state=()=>({mock,connected,received,invalid,reconnects,recorded,recordDrops,archiveError,
    age_ms:lastAt?Date.now()-lastAt:null,frame:last});
const assets=new Map([['/scene.js',path.join(root,'demo_v1/web/scene.js')],
    ['/vendor/three.module.js',path.join(root,'software/pc_viewer/node_modules/three/build/three.module.js')],
    ['/vendor/three.core.js',path.join(root,'software/pc_viewer/node_modules/three/build/three.core.js')],
    ['/vendor/OrbitControls.js',path.join(root,'software/pc_viewer/node_modules/three/examples/jsm/controls/OrbitControls.js')]]);
const page=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>常驻姿态演示</title>
<style>body{margin:0;background:#0b111b;color:#e5eef9;font:16px system-ui}header{padding:20px}#viewport{height:75vh}#status{color:#9fc8e7}</style>
<script type="importmap">{"imports":{"three":"/vendor/three.module.js","three/addons/controls/OrbitControls.js":"/vendor/OrbitControls.js"}}</script>
<header><b>Wi-Fi 姿态 · 可选 PC 观察端</b><p id="status">等待新结果</p><small>原始模型坐标，无插帧；PC 断开不会停止板端。</small></header><div id="viewport"></div>
<script type="module">import {createScene} from './scene.js';
const bones=[[0,1],[0,2],[0,3],[2,4],[2,5],[3,6],[3,7],[4,8],[5,7],[5,9],[6,10],[7,11],[9,12],[11,13]];
const scene=createScene(document.getElementById('viewport'),bones,()=>{});let identity='';
async function update(){try{const s=await(await fetch('/api/state')).json();const f=s.frame;
document.getElementById('status').textContent=(s.mock?'模拟测试 · ':'')+(s.connected?'已连接':'重连中')+' · 新结果 '+s.received+' · 结果年龄 '+(s.age_ms??'—')+' ms · 归档丢弃 '+s.recordDrops+(s.archiveError?' · 归档暂停':'');
if(f&&f.session+':'+f.sequence!==identity){identity=f.session+':'+f.sequence;scene.setPose(f);}}
catch{document.getElementById('status').textContent='观察端连接中断';}setTimeout(update,100);}update();</script></html>`;
const server=http.createServer((req,res)=>{
    res.setHeader('Cache-Control','no-store');
    if(req.method!=='GET'){res.writeHead(405).end();return;}
    if(req.url==='/api/state'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(state()));return;}
    if(req.url==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(page);return;}
    const file=assets.get(req.url);if(!file){res.writeHead(404).end();return;}
    res.setHeader('Content-Type','text/javascript');fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
});
server.maxConnections=8;server.requestTimeout=5000;
server.listen(httpPort,'127.0.0.1',()=>console.log('RESIDENT_PC_READY',JSON.stringify({url:`http://127.0.0.1:${httpPort}`,board,port,archive:!!output,mock})));
async function stop(){if(closed)return;closed=true;clearTimeout(timer);socket?.destroy();server.close();await worker?.terminate();console.log(JSON.stringify(state()));}
process.on('SIGINT',stop);process.on('SIGTERM',stop);connect();if(seconds)setTimeout(stop,seconds*1000);
