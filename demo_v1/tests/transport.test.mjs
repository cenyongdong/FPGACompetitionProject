import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeFrame} from '../host/protocol.mjs';
import {FULL_BYTES,decodeFull,FullStream,ConfirmedStream} from '../host/full_record.mjs';
function record(){
    const b=Buffer.alloc(FULL_BYTES);b.write('PIWFUL1\0');b.writeUInt32LE(1,8);b.writeUInt32LE(FULL_BYTES,12);
    const f={session:'7',frame:'1000000',invocation:'0',source_ns:'123',published_ns:'1000',sequence:'1',candidate:0,flags:0,score:.75,joints:Array(42).fill(0)};
    for(const [off,key] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[72,'sequence']])b.writeBigUInt64LE(BigInt(f[key]),off);
    b.writeBigUInt64LE(10n,48);b.writeBigUInt64LE(20n,56);b.writeBigUInt64LE(30n,64);
    encodeFrame(f).copy(b,128);b.writeFloatLE(.75,384+43200);return b;
}
test('fragmentation/coalescing preserves full result and selected pose',()=>{
    const raw=record(),parser=new FullStream();assert.equal(parser.push(raw.subarray(0,1)).length,0);
    assert.equal(parser.push(raw.subarray(1,999)).length,0);
    assert.equal(parser.push(Buffer.concat([raw.subarray(999),raw])).length,2);parser.finish();
});
test('reject corrupt full candidate, NaN and partial EOF',()=>{
    let raw=record();raw.writeFloatLE(1,384+43200+4);assert.throws(()=>decodeFull(raw));
    raw=record();raw.writeFloatLE(NaN,384);assert.throws(()=>decodeFull(raw));
    const p=new FullStream();p.push(record().subarray(0,200));assert.throws(()=>p.finish());
});
test('v2 retains raw bytes before validation and requires board confirmation',()=>{
    const raw=record();raw.write('PIWFUL2\0');raw.writeUInt32LE(2,8);
    const parser=new ConfirmedStream();const rows=parser.push(raw);
    assert.equal(rows[0].type,'raw');assert.deepEqual(rows[0].raw,raw);assert.throws(()=>parser.finish());
    const ack=Buffer.alloc(8);ack.writeBigUInt64LE(1n);
    assert.equal(parser.push(ack.subarray(0,3)).length,0);
    assert.equal(parser.push(ack.subarray(3))[0].sequence,1n);parser.finish();
    assert.equal(decodeFull(raw).frame,'1000000');
});
