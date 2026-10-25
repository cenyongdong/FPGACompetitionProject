import fs from 'node:fs';
import path from 'node:path';
export const DELIVERY_STAGES=['raw_ready','save_begin','save_end','decode_end','ack_queued','ack_flushed','confirmation'];
export class HostDeliveryTiming {
    constructor(count,clock=()=>process.hrtime.bigint()) {
        this.clock=clock;this.rows=new BigUint64Array(count*DELIVERY_STAGES.length);this.count=0;
    }
    mark(index,stage) {
        const column=DELIVERY_STAGES.indexOf(stage);
        if(index<0||index>=this.rows.length/DELIVERY_STAGES.length||column<0)throw new Error('Delivery timing bound');
        this.rows[index*DELIVERY_STAGES.length+column]=this.clock();this.count=Math.max(this.count,index+1);
    }
    save(output) {
        const fd=fs.openSync(path.join(output,'host-delivery.jsonl'),'wx');
        try {for(let i=0;i<this.count;++i) {
            const row={invocation:i};DELIVERY_STAGES.forEach((name,c)=>row[name+'_ns']=this.rows[i*DELIVERY_STAGES.length+c].toString());
            fs.writeSync(fd,JSON.stringify(row)+'\n');
        }} finally{fs.closeSync(fd);}
    }
}
// 负载仍完整保存到原归档；仅短测可指定注入保存延迟，以检验背压，默认零延迟。
export function archiveRecord(raw,bytes,delayMs,callback) {
    return new Promise(resolve=> {
        const complete=error=>{try{callback(error);}finally{resolve();}};
        const write=()=>{try {raw.write(bytes,complete);}catch(e){complete(e);}};
        if(delayMs)setTimeout(write,delayMs);else write();
    });
}
