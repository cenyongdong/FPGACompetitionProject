import { decodeFrame } from './protocol.mjs';
export const FULL_BYTES = 60784;
export function decodeFull(b) {
    if (b.length !== FULL_BYTES || ![['PIWFUL1\0',1],['PIWFUL2\0',2]].some(([magic,version])=>b.toString('ascii',0,8)===magic&&b.readUInt32LE(8)===version) || b.readUInt32LE(12) !== FULL_BYTES)
        throw new Error('Invalid complete-result record');
    const frame = decodeFrame(b.subarray(128,384));
    for (const [offset,name] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[72,'sequence']])
        if (b.readBigUInt64LE(offset).toString() !== frame[name]) throw new Error('Full/pose identity mismatch');
    if (frame.flags !== 0 || b.readUInt32LE(124) !== 0) throw new Error('Expected live result');
    const metrics = {};
    for (const [off,name] of [[80,'process_ms'],[88,'preprocess_ms'],[96,'forward_ms'],[104,'output_ms']]) {
        metrics[name] = b.readDoubleLE(off);
        if (!Number.isFinite(metrics[name]) || metrics[name] < 0) throw new Error('Invalid processing time');
    }
    const arrived = b.readBigUInt64LE(48), began = b.readBigUInt64LE(56), returned = b.readBigUInt64LE(64);
    if (!(arrived <= began && began <= returned)) throw new Error('Invalid board timeline');
    metrics.queue_ms = Number(began-arrived)/1e6;
    metrics.input_queue_high = b.readUInt32LE(112);
    metrics.gate = b.readUInt32LE(116);
    if (metrics.gate > 1) throw new Error('Numeric gate rejected');
    for(let off=384;off<FULL_BYTES;off+=4) if(!Number.isFinite(b.readFloatLE(off))) throw new Error('Non-finite complete model result');
    const scores = 384+43200, poses = scores+400;
    let best=0;
    for(let i=1;i<100;++i) if(b.readFloatLE(scores+i*4)>b.readFloatLE(scores+best*4)) best=i;
    if (frame.candidate !== best || b.readUInt32LE(120) !== best || frame.score !== b.readFloatLE(scores+best*4)) throw new Error('Selection mismatch');
    frame.joints.forEach((x,i)=> {if(x!==b.readFloatLE(poses+(best*42+i)*4)) throw new Error('Selected/full pose mismatch');});
    return { ...frame, metrics };
}
export class FullStream {
    tail = Buffer.alloc(0);
    push(chunk) {
        const bytes = this.tail.length ? Buffer.concat([this.tail,chunk]) : chunk;
        const rows=[]; let offset=0;
        while(bytes.length-offset>=FULL_BYTES) {
            const raw=Buffer.from(bytes.subarray(offset,offset+FULL_BYTES));
            rows.push({raw,frame:decodeFull(raw)}); offset+=FULL_BYTES;
        }
        this.tail=Buffer.from(bytes.subarray(offset)); return rows;
    }
    finish() {if(this.tail.length) throw new Error('Truncated complete result at EOF');}
}

// v2：原值记录 -> 主机落盘回执 -> 板端门检确认，最后才交付展示。
export class ConfirmedStream {
    tail=Buffer.alloc(0);
    pending=false;
    push(chunk) {
        const bytes=this.tail.length?Buffer.concat([this.tail,chunk]):chunk;
        const events=[];let offset=0;
        while(bytes.length-offset>=(this.pending?8:FULL_BYTES)) {
            if(this.pending){events.push({type:'confirmed',sequence:bytes.readBigUInt64LE(offset)});offset+=8;this.pending=false;}
            else {events.push({type:'raw',raw:Buffer.from(bytes.subarray(offset,offset+FULL_BYTES))});offset+=FULL_BYTES;this.pending=true;}
        }
        this.tail=Buffer.from(bytes.subarray(offset));return events;
    }
    finish(){if(this.tail.length||this.pending)throw new Error('Truncated or unconfirmed complete result at EOF');}
}
