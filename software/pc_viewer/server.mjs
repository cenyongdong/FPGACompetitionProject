import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { WebSocketServer, WebSocket } from 'ws';
import { RecordStream } from './protocol.mjs';
import { HERE, WORK, EXE } from './paths.mjs';

const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'data/archive.json')));
const httpPort = Number(process.env.POSE_HTTP_PORT || 39380), tcpPort = Number(process.env.POSE_TCP_PORT || 39381);
const duration = Number(process.env.POSE_PREVIEW_MINUTES || 30);
if (![httpPort, tcpPort].every(p => Number.isInteger(p) && p > 0 && p <= 65535) || !(duration > 0 && duration <= 120)) throw new Error('Invalid preview options');
const frames = [], records = [], errors = [];
let sender = null, activeSocket = null, complete = false, senderExit = null, closing = false;
let heartbeat;
const deadline = Date.now() + duration * 60000;
const wss = new WebSocketServer({ noServer: true, maxPayload: 1024, perMessageDeflate: false });
const status = () => ({ type: 'status', received: frames.length, expected: manifest.frames.length, complete,
    tcp_connected: !!activeSocket, sender_exit: senderExit, errors, deadline, source: manifest.source, fresh_inferences: 0 });
const broadcast = data => {
    const bytes = JSON.stringify(data);
    for (const ws of wss.clients) if (ws.readyState === WebSocket.OPEN) {
        if (ws.bufferedAmount > 65536) ws.terminate(); else ws.send(bytes);
    }
};
const recordError = error => { errors.push(String(error.message || error)); broadcast(status()); console.error(error); };
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
const files = new Map([
    ['/', 'public/index.html'], ['/app.js', 'public/app.js'], ['/scene.js', 'public/scene.js'], ['/style.css', 'public/style.css'],
    ['/vendor/three.module.js', 'node_modules/three/build/three.module.js'], ['/vendor/three.core.js', 'node_modules/three/build/three.core.js'],
    ['/vendor/OrbitControls.js', 'node_modules/three/examples/jsm/controls/OrbitControls.js']
]);
const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (req.method !== 'GET') { res.writeHead(405).end(); return; }
    if (url.pathname === '/favicon.ico') { res.writeHead(204).end(); return; }
    if (url.pathname === '/api/clip' || url.pathname === '/api/status') {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(url.pathname === '/api/status' ? status() : { manifest, frames, status: status() })); return;
    }
    const file = files.get(url.pathname);
    if (!file) { res.writeHead(404).end('Not found'); return; }
    try {
        const bytes = fs.readFileSync(path.join(HERE, file));
        res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream'); res.end(bytes);
    } catch (e) { res.writeHead(500).end('Asset missing'); recordError(e); }
});
server.on('upgrade', (req, socket, head) => {
    if (req.url !== '/updates' || (req.headers.origin && req.headers.origin !== `http://127.0.0.1:${httpPort}`)) { socket.destroy(); return; }
    wss.handleUpgrade(req, socket, head, ws => {
        wss.emit('connection', ws, req);
        // 初次连接也通过WebSocket交付实际TCP接收快照。
        ws.send(JSON.stringify({ type: 'clip', manifest, frames, status: status() }));
    });
});
const tcp = net.createServer(socket => {
    if (activeSocket || complete || errors.length) { socket.destroy(); return; }
    activeSocket = socket;
    const parser = new RecordStream();
    socket.setTimeout(5000, () => socket.destroy(new Error('TCP input idle deadline')));
    broadcast(status());
    socket.on('data', chunk => {
        try {
            for (const { frame, bytes } of parser.push(chunk)) {
                const expected = manifest.frames[frames.length];
                if (!expected || createHash('sha256').update(bytes).digest('hex') !== expected.record_sha256) throw new Error('Received bytes differ from archived real board result');
                frame.received_pc_ns = process.hrtime.bigint().toString();
                frame.case = expected.case;
                frames.push(frame); records.push(bytes);
                broadcast({ type: 'frame', frame });
            }
            broadcast(status());
        } catch (e) { recordError(e); socket.destroy(); }
    });
    socket.on('end', () => {
        try {
            parser.finish();
            if (frames.length !== manifest.frames.length) throw new Error('Incomplete clip at TCP EOF');
            complete = true;
            fs.writeFileSync(path.join(WORK, 'received.piwpose'), Buffer.concat(records));
            saveReceipt(); broadcast(status());
        } catch (e) { recordError(e); }
    });
    socket.on('error', recordError);
    socket.on('close', () => { activeSocket = null; broadcast(status()); });
});
function saveReceipt() {
    fs.writeFileSync(path.join(WORK, 'receipt.json'), JSON.stringify({ ...status(),
        received_sha256: createHash('sha256').update(Buffer.concat(records)).digest('hex'),
        expected_sha256: manifest.records_sha256, frames: frames.map(f => ({ frame: f.frame, invocation: f.invocation, candidate: f.candidate, score: f.score, received_pc_ns: f.received_pc_ns })),
        network: 'C++ sender -> loopback TCP -> Node -> WebSocket/browser', board_operations: 0,
        pid: process.pid, url: `http://127.0.0.1:${httpPort}` }, null, 2) + '\n');
}
async function shutdown() {
    if (closing) return;
    closing = true;
    clearInterval(heartbeat); clearTimeout(lifetime);
    if (sender && sender.exitCode === null) sender.kill();
    activeSocket?.destroy();
    for (const ws of wss.clients) ws.terminate();
    wss.close(); tcp.close(); server.close();
    saveReceipt();
    console.log('POSE_PREVIEW_CLOSED');
}
server.on('error', e => { recordError(e); shutdown(); process.exitCode = 1; });
tcp.on('error', e => { recordError(e); shutdown(); process.exitCode = 1; });
process.on('SIGINT', shutdown); process.on('SIGTERM', shutdown);
const lifetime = setTimeout(shutdown, duration * 60000);
tcp.listen(tcpPort, '127.0.0.1', () => {
    server.listen(httpPort, '127.0.0.1', () => {
        console.log(`POSE_PREVIEW_READY http://127.0.0.1:${httpPort} TCP ${tcpPort} PID ${process.pid} bounded_minutes=${duration}`);
        fs.writeFileSync(path.join(WORK, 'runtime.json'), JSON.stringify({ pid: process.pid, started: new Date().toISOString(), deadline, httpPort, tcpPort }));
        sender = spawn(EXE, [path.join(WORK, 'records.piwpose'), '127.0.0.1', String(tcpPort), '30'], { windowsHide: true });
        const log = fs.createWriteStream(path.join(WORK, 'sender.txt'));
        sender.stdout.pipe(log, { end: false }); sender.stderr.pipe(log, { end: false });
        sender.on('error', recordError);
        sender.on('close', code => { senderExit = code; log.end(); if (code !== 0) recordError(new Error('C++ sender exited ' + code)); saveReceipt(); broadcast(status()); });
        heartbeat = setInterval(() => broadcast(status()), 1000);
    });
});
