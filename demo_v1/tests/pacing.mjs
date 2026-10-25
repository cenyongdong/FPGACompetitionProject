import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
const child=spawn('python',['demo_v1/host/pacer.py','300','30'],{windowsHide:true});
const stamps=[];for await(const line of createInterface({input:child.stdout})) {
    if(Number(line)!==stamps.length)throw new Error('Tick sequence');stamps.push(process.hrtime.bigint());
}
if(stamps.length!==300)throw new Error('Incomplete pacing');
const errors=stamps.map((x,i)=>Number(x-stamps[0])/1e6-i*1000/30);
const intervals=stamps.slice(1).map((x,i)=>Number(x-stamps[i])/1e6);
console.log(JSON.stringify({ticks:stamps.length,max_late_ms:Math.max(...errors),min_late_ms:Math.min(...errors),max_interval_ms:Math.max(...intervals),min_interval_ms:Math.min(...intervals)}));
if(Math.max(...errors)>20)throw new Error('Pacing deadline exceeded');
