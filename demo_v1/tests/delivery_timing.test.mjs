import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {once} from 'node:events';
import {HostDeliveryTiming,archiveRecord} from '../host/delivery_timing.mjs';

test('save callback/ACK occurs only after complete original write despite delayed archive',async()=>{
    const dir=fs.mkdtempSync(path.join(os.tmpdir(),'demo-delivery-'));
    try {
        const file=path.join(dir,'raw'),out=fs.createWriteStream(file,{flags:'wx'}),actual=Buffer.alloc(60784,0x9a);
        const timing=new HostDeliveryTiming(1);timing.mark(0,'raw_ready');timing.mark(0,'save_begin');
        let acknowledged=false;const saving=archiveRecord(out,actual,40,error=>{
            assert.ifError(error);timing.mark(0,'save_end');
            assert.deepEqual(fs.readFileSync(file),actual);acknowledged=true;timing.mark(0,'ack_queued');
        });
        assert.equal(acknowledged,false);await saving;assert.equal(acknowledged,true);
        out.end();await once(out,'close');timing.save(dir);
        const row=JSON.parse(fs.readFileSync(path.join(dir,'host-delivery.jsonl')));
        assert.ok(BigInt(row.save_end_ns)-BigInt(row.save_begin_ns)>=35000000n);
        assert.ok(BigInt(row.ack_queued_ns)>=BigInt(row.save_end_ns));
        assert.equal(row.confirmation_ns,'0');
    } finally{fs.rmSync(dir,{recursive:true,force:true});}
});
