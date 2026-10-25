import {createScene} from './scene.js';
const $=id=>document.getElementById(id);
const bones=[[0,1],[0,2],[0,3],[2,4],[2,5],[3,6],[3,7],[4,8],[5,7],[5,9],[6,10],[7,11],[9,12],[11,13]];
let scene,lastArrival=0,labels=false,displayed=0;
try {scene=createScene($('viewport'),bones,fps=>$('fps').textContent=fps);}catch(e){$('error').textContent='3D初始化失败：'+e.message;}
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{scene?.view(button.dataset.view);document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('selected',b===button));}));
$('labels').addEventListener('click',()=>{labels=!labels;scene?.labels(labels);});
const ws=new WebSocket('ws://'+location.host+'/updates');
ws.onopen=()=>$('connection').textContent='已连接本地接收器';
ws.onclose=()=>$('connection').textContent='接收器已关闭';
ws.onmessage=event=>{
    const m=JSON.parse(event.data);
    if(m.type==='status') {
        const s=m.status;$('sent').textContent=s.sent;$('received').textContent=s.received;
        $('hz').textContent=s.received_hz.toFixed(2);$('state').textContent=s.complete?'本轮完成':s.connected?'推理中':'等待板端';
        $('footer').textContent=s.stage+' · 新推理 '+s.received+' / '+s.target+' · HDMI未接入';$('error').textContent=s.errors.join('\n');
    }
    if(m.type==='frame') {
        const f=m.frame;scene?.setPose(f);lastArrival=performance.now();++displayed;
        $('sample').textContent=(f.split||'test')+' · '+f.sample;$('frame').textContent=f.frame;$('invocation').textContent=f.invocation;
        $('score').textContent=f.candidate+' / '+f.score.toFixed(5);$('latency').textContent=f.end_to_end_ms.toFixed(2)+' ms';$('process').textContent=f.metrics.process_ms.toFixed(2)+' ms';
        window.demoLive={frame:f.frame,invocation:f.invocation,joints:f.joints,displayed,flags:f.flags};
    }
};
setInterval(()=>{if(lastArrival&&performance.now()-lastArrival>500)$('connection').textContent='最近结果距今 '+((performance.now()-lastArrival)/1000).toFixed(1)+' s';},500);
