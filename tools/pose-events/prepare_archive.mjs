// Read-only adapter for existing complete outputs; reuse the existing protocol decoder.
import fs from 'node:fs';
import path from 'node:path';
import {createInterface} from 'node:readline';
import {decodeFull,FULL_BYTES} from '../../demo_v1/host/full_record.mjs';

const options=Object.fromEntries(process.argv.slice(2).map(x=>{
    const i=x.indexOf('=');if(i<1)throw new Error('Use --key=value');return [x.slice(0,i),x.slice(i+1)];
}));
const run=path.resolve(options['--run']||'demo_v1/runs/delivery-long-r1');
const output=path.resolve(options['--output']||'.local/pose-events-validation-20261024-r1');
const limit=Number(options['--limit']||15648);
if(!Number.isInteger(limit)||limit<1||limit>52800)throw new Error('Bounded limit 1..52800 required');
if(fs.existsSync(output))throw new Error('Fresh output directory required');
const fullPath=path.join(run,'actual.full'),rowsPath=path.join(run,'received.jsonl');
const before=fs.statSync(fullPath),rowsBefore=fs.statSync(rowsPath);
if(before.size%FULL_BYTES)throw new Error('Truncated complete-result archive');
fs.mkdirSync(output,{recursive:true});
const csvPath=path.join(output,'archive-input.csv');
const csv=fs.openSync(csvPath,'wx'),full=fs.openSync(fullPath,'r');
const write=s=>fs.writeSync(csv,s+'\n');
write('# origin=archived_board_inference');
write('# feedback_origin=generated_virtual_controls_not_historical_hardware');
write('# time_basis=host_receive_monotonic_not_RF_capture');
write('kind,now_ns,epoch,sequence,capture_ns,capture_sequence,segment,clock,subject_verified,score,'+
    Array.from({length:42},(_,i)=>`j${Math.floor(i/3)}c${i%3}`).join(','));
const data=Buffer.alloc(FULL_BYTES),unique=new Set(),segments=new Set();
const counts={frames:0,test:0,train:0,segment_boundaries:0,source_index_gaps:0};
let base=null,lastNow=0n,lastHeartbeat=-1000000000n,heartbeatSequence=0n,epoch=null,previous=null;
const input=createInterface({input:fs.createReadStream(rowsPath),crlfDelay:Infinity});
try {
    for await(const line of input){
        if(!line.trim())continue;
        const row=JSON.parse(line);
        let bytes=0;while(bytes<FULL_BYTES){const n=fs.readSync(full,data,bytes,FULL_BYTES-bytes,null);if(!n)throw new Error('Unexpected EOF');bytes+=n;}
        const frame=decodeFull(data);
        if(frame.frame!==row.frame||frame.invocation!==row.invocation)throw new Error('Archive/receipt identity mismatch');
        if(BigInt(frame.sequence)!==BigInt(counts.frames+1))throw new Error('Transport sequence mismatch');
        if(epoch===null)epoch=frame.session;else if(epoch!==frame.session)throw new Error('Mixed sessions');
        const match=/^(.*)_(\d+)$/.exec(row.sample);if(!match)throw new Error('Source sample identity unavailable');
        const segment=`${row.split}:${match[1]}`,sourceIndex=Number(match[2]);
        if(previous){if(segment!==previous.segment)++counts.segment_boundaries;else if(sourceIndex!==previous.index+1)++counts.source_index_gaps;}
        previous={segment,index:sourceIndex};unique.add(`${row.split}:${row.sample}`);segments.add(segment);
        const stamp=BigInt(row.pc_received_ns);if(base===null){base=stamp;write(`B,0,${epoch},0`);}
        const now=stamp-base;if(now<lastNow)throw new Error('Receive clock regressed');
        if(now-lastHeartbeat>=100000000n){write(`H,${now},${epoch},${++heartbeatSequence}`);lastHeartbeat=now;}
        write(`I,${now},${epoch},${frame.sequence}`);
        // Capture time, anatomical mapping and subject identity are deliberately NOT inferred.
        write(['F',now,epoch,frame.sequence,0,sourceIndex,segment,'unknown',0,frame.score,...frame.joints].join(','));
        ++counts.frames;++counts[row.split];lastNow=now;
        if(counts.frames===limit)break;
    }
    if(counts.frames!==limit)throw new Error('Insufficient existing records');
    // Explicit simulated faults after archive consumption; not attributed to the original run.
    const stale=lastNow+300000000n;
    write(`H,${stale},${epoch},${++heartbeatSequence}`);
    write(`I,${stale},${epoch},${counts.frames+1}`);
    write(`T,${stale},${epoch},0`); // input/service refreshed, no new result
    write(`T,${stale+300000000n},${epoch},0`); // input expired, service still within 500ms
    write(`T,${stale+500000000n},${epoch},0`); // service expired
} finally {input.close();fs.closeSync(csv);fs.closeSync(full);}
const after=fs.statSync(fullPath),rowsAfter=fs.statSync(rowsPath);
if(after.size!==before.size||after.mtimeMs!==before.mtimeMs||rowsAfter.size!==rowsBefore.size||rowsAfter.mtimeMs!==rowsBefore.mtimeMs)
    throw new Error('Source archive/receipt changed during read-only import');
const audit={
    date:'2026-10-24',hardware_test:false,source:fullPath,receipts:rowsPath,
    source_unchanged_size_and_mtime:true,consumed_prefix_bytes:counts.frames*FULL_BYTES,
    ...counts,unique_sources:unique.size,source_segments:segments.size,
    semantic_contract:{
        topology:'project-14-v1: matches Wi-Fi limb_loss and existing viewer',
        anatomical_index_mapping_verified:false,
        coordinate_unit_declared:'metres in existing visualization artifacts',
        documented_display_up:[0,0,-1],physical_up_calibration_verified:false,
        source_capture_times_verified:false,single_subject_identity_verified:false,
        conclusion:'Real actions, hold durations and assistance intent remain unknown',
        evidence:[
            'D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/datasets/wifi_pose.py: loads N*14*3 without anatomical index names',
            'D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/models/losses/limb_loss.py: numbered topology only',
            'D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/visualization/README.md: metre units; Z-down display convention; --fps playback is not RF clock',
            'software/core/display/skeleton_render.cpp: display projection uses -(C2-3.4), not a room calibration',
            'demo_v1/host/run.mjs: source_ns taken from host clock at transmission',
            'demo_v1/host/full_record.mjs: flags=live_board_output means fresh inference, not live RF capture'
        ]
    },
    simulated_feedback:{service_period_ns:100000000,service_timeout_ns:500000000,result_timeout_ns:300000000,
        tail_faults:['result_stale_with_fresh_input','input_stale','service_lost'],
        statement:'Controls are generated virtual-time stimuli, not historical PL observations'},
    validation_scope:'Existing full records decoded and selected pose checked; no new inference, accuracy labels or RF sampling claim'
};
fs.writeFileSync(path.join(output,'contract-audit.json'),JSON.stringify(audit,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(audit,null,2));
