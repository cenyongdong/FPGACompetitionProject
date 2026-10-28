import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import {receive} from './receive_full.mjs';
import {record} from '../../software/pose180_pipeline/host/test/fixtures.mjs';
import {SCORE_OFFSET,FULL_BYTES} from '../../software/pose180_pipeline/host/full_record.mjs';

test('synthetic loopback: fragmented records, original invalid values, EOF and partial tail',async()=>{
    const parent=path.resolve('.local/kinect-check-20261028-r1/offline-tests');fs.mkdirSync(parent,{recursive:true});
    const work=fs.mkdtempSync(path.join(parent,'network-fixture-'));
    const good=[0,1,2].map(index=>record({index,fullPattern:true}));
    const bad=record({index:3});bad.writeFloatLE(NaN,SCORE_OFFSET);
    const wire=Buffer.concat([...good,bad,Buffer.alloc(13,7)]);
    const server=net.createServer(socket=>{socket.write(wire.subarray(0,17));setTimeout(()=>socket.end(wire.subarray(17)),10);});
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    try {
        const result=await receive({host:'127.0.0.1',port:server.address().port,seconds:5,output:path.join(work,'capture'),simulation:true});
        assert.equal(result.records,4);assert.equal(result.invalid,1);assert.equal(result.trailing_bytes,13);assert.equal(result.socket_closed,true);
        assert.deepEqual(fs.readFileSync(path.join(work,'capture','actual.full')),wire.subarray(0,4*FULL_BYTES));
        const rows=fs.readFileSync(path.join(work,'capture','arrival.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
        assert.deepEqual(rows.map(r=>r.valid),[true,true,true,false]);assert(rows.every(r=>r.host_received_utc&&r.host_received_monotonic_ns));
    } finally {await new Promise(resolve=>server.close(resolve));}
});
