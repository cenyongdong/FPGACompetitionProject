import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createHash } from 'node:crypto';
import { BONES, decodeFrame, encodeFrame, RecordStream } from '../protocol.mjs';
import { HERE, ROOT, WORK, EXE } from '../paths.mjs';

const bytes = fs.readFileSync(path.join(WORK, 'records.piwpose'));
const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'data/archive.json')));
test('versioned topology agrees with the current project 14-joint renderer', () => {
    const header = fs.readFileSync(path.join(ROOT, 'software/core/display/skeleton_render.hpp'), 'utf8');
    const body = header.split('bones')[1].split('enum class')[0];
    const pairs = Array.from(body.matchAll(/\{\s*(\d+)\s*,\s*(\d+)\s*\}/g), m => [Number(m[1]), Number(m[2])]);
    assert.deepEqual(BONES, pairs);
});
test('archived input and selected FP32 bytes match original full board output', () => {
    assert.equal(bytes.length, 768);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), manifest.records_sha256);
    for (let i = 0; i < 3; ++i) {
        const r = bytes.subarray(i*256, (i+1)*256), f = decodeFrame(r), m = manifest.frames[i];
        const poses = fs.readFileSync(path.join(ROOT, m.source_directory, 'poses.f32'));
        const scores = fs.readFileSync(path.join(ROOT, m.source_directory, 'scores.f32'));
        assert.equal(f.frame, m.frame); assert.equal(f.candidate, m.candidate);
        assert.deepEqual(r.subarray(88), poses.subarray(f.candidate*168, f.candidate*168+168));
        assert.deepEqual(r.subarray(64,68), scores.subarray(f.candidate*4,f.candidate*4+4));
        assert.deepEqual(encodeFrame(f), r);
    }
});
test('stream accepts one-byte fragments and coalesced records identically', () => {
    const split = new RecordStream(), together = new RecordStream();
    let got = [];
    for (const byte of bytes) got.push(...split.push(Buffer.from([byte])));
    split.finish();
    assert.equal(got.length, 3); assert.deepEqual(got, together.push(bytes)); together.finish();
});
test('64-bit frame, invocation and time identities survive browser-facing JSON', () => {
    const f = decodeFrame(bytes.subarray(0,256));
    f.frame = '18446744073709551615'; f.invocation = '9007199254740993'; f.source_ns = '1800000000000000000';
    const decoded = JSON.parse(JSON.stringify(decodeFrame(encodeFrame(f))));
    assert.equal(decoded.frame, f.frame); assert.equal(decoded.invocation, f.invocation); assert.equal(decoded.source_ns, f.source_ns);
});
test('invalid records fail before publication, including truncation, NaN and sequence reuse', () => {
    for (const mutate of [b=>b[0]=0,b=>b.writeUInt16LE(2,8),b=>b.writeUInt32LE(9999999,12),b=>b.writeUInt16LE(17,60),
        b=>b.writeUInt32LE(100,56),b=>b.writeUInt16LE(2,62),b=>b.writeFloatLE(NaN,88),b=>b.writeFloatLE(Infinity,64),
        b=>b.writeUInt32LE(2,68),b=>b.writeUInt32LE(2,72),b=>b.writeUInt32LE(1,76),b=>b.writeBigUInt64LE(0n,16)]) {
        const b = Buffer.from(bytes.subarray(0,256)); mutate(b); assert.throws(()=>decodeFrame(b));
    }
    const truncated = new RecordStream(); truncated.push(bytes.subarray(0,255)); assert.throws(()=>truncated.finish());
    const duplicate = new RecordStream();duplicate.push(bytes.subarray(0,256));assert.throws(()=>duplicate.push(bytes.subarray(0,256)));
    const session = new RecordStream();session.push(bytes.subarray(0,256));const b=Buffer.from(bytes.subarray(256,512));b.writeBigUInt64LE(111n,16);assert.throws(()=>session.push(b));
});

async function receiveViaCpp(fragment, fixture = path.join(WORK, 'records.piwpose')) {
    const chunks = [];
    let resolveEnd, rejectEnd;
    const ended = new Promise((resolve,reject)=>{resolveEnd=resolve;rejectEnd=reject;});
    const server = net.createServer(socket => {
        socket.on('data', b => chunks.push(b)); socket.on('end', resolveEnd); socket.on('error', rejectEnd);
    });
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const child = spawn(EXE,[fixture,'127.0.0.1',String(server.address().port),'0',String(fragment)],{windowsHide:true});
    let output='';child.stdout.on('data',b=>output+=b);child.stderr.on('data',b=>output+=b);
    try {
        const [code] = await once(child,'close'); assert.equal(code,0,output);
        await ended;
        return Buffer.concat(chunks);
    } finally { server.close(); if(child.exitCode===null)child.kill(); }
}
test('actual C++ TCP sender preserves all 768 bytes with normal and one-byte writes', { timeout: 15000 }, async () => {
    assert.deepEqual(await receiveViaCpp(256), bytes);
    assert.deepEqual(await receiveViaCpp(1), bytes);
});
test('C++ codec preserves large identities and stops on a refused connection', { timeout: 15000 }, async () => {
    const frame=decodeFrame(bytes.subarray(0,256));frame.frame='18446744073709551615';frame.invocation='9007199254740993';
    const fixture=path.join(WORK,'test-large-identities.piwpose'), b=encodeFrame(frame);
    fs.writeFileSync(fixture,b);assert.deepEqual(await receiveViaCpp(7,fixture),b);
    const server=net.createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;await new Promise(r=>server.close(r));
    const child=spawn(EXE,[fixture,'127.0.0.1',String(port),'0'],{windowsHide:true});
    let output='';child.stderr.on('data',b=>output+=b);const [code]=await once(child,'close');assert.equal(code,1);assert.match(output,/no retry/);
});
test('C++ rejects corrupt/truncated files before attempting a TCP connection', { timeout: 15000 }, async () => {
    for (const [name, b] of [['truncated',bytes.subarray(0,255)],['nan',Buffer.from(bytes.subarray(0,256))]]) {
        if (name==='nan') b.writeFloatLE(NaN,88);
        const fixture=path.join(WORK,'test-invalid-'+name+'.piwpose');fs.writeFileSync(fixture,b);
        const child=spawn(EXE,[fixture,'127.0.0.1','1','0'],{windowsHide:true});let output='';child.stderr.on('data',b=>output+=b);
        const [code]=await once(child,'close');assert.equal(code,1);assert.match(output,/truncated|Invalid PIWPOSE1/);
    }
});
