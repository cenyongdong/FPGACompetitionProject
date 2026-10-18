import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createRequire } from 'node:module';
import { WORK, MANIFEST, DEPENDENCIES } from '../paths.mjs';
import { encodeFrame } from '../protocol.mjs';

const { WebSocket } = createRequire(import.meta.url)(path.join(DEPENDENCIES, 'ws'));
const base = process.env.POSE_PREVIEW_URL || 'http://127.0.0.1:39380';
const manifest = JSON.parse(fs.readFileSync(MANIFEST));
const original = fs.readFileSync(path.join(WORK, 'records.piwpose'));
const status = await (await fetch(base + '/api/status')).json();
assert.equal(status.complete, true);
assert.equal(status.sender_exit, 0);
assert.deepEqual(status.errors, []);
const ws = new WebSocket(base.replace('http:', 'ws:') + '/updates', { origin: base });
const deadline = setTimeout(() => ws.terminate(), 5000);
let message;
try { [message] = await once(ws, 'message'); } finally { clearTimeout(deadline); ws.close(); }
const clip = JSON.parse(message);
assert.equal(clip.type, 'clip');
assert.equal(clip.frames.length, manifest.frames.length);
assert.deepEqual(Buffer.concat(clip.frames.map(encodeFrame)), original);
const assets = ['/', '/app.js', '/scene.js', '/playback.js', '/style.css', '/vendor/three.module.js', '/vendor/three.core.js', '/vendor/OrbitControls.js'];
for (const asset of assets) assert.equal((await fetch(base + asset)).status, 200, asset);
const result = { checked_at: new Date().toISOString(), cpp_sender_exit: status.sender_exit,
    tcp_records: status.received, websocket_records: clip.frames.length, tcp_and_websocket_bytes_identical: true,
    served_assets: assets.length, errors: status.errors, fresh_inferences: 0, board_operations: 0 };
fs.writeFileSync(path.join(WORK, 'preview-check.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
