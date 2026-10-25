// Synthetic transport-only test; no production model/wire/SDK/board operations.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
const out = path.resolve(process.argv[2] || '');
if (process.argv.length !== 3) throw Error('Usage: node host.mjs NEW_OUTPUT_DIRECTORY');
fs.mkdirSync(out); // Never replace an earlier comparison.
const bytes = 60784, rounds = 64, rows = [], now = () => process.hrtime.bigint().toString();
const expected = Buffer.alloc(bytes, 0xa5); expected.write('SYNTHACK', 0, 'ascii');
const archive = fs.createWriteStream(path.join(out, 'synthetic-records.bin'), { flags: 'wx' });
let socket, tail = Buffer.alloc(0), state = 'record', sequence = 1, row, ended = false;
const server = net.createServer(client => {
    if (socket || ended) { client.destroy(); return; }
    socket = client; client.setNoDelay(true); client.setTimeout(10000);
    client.on('data', chunk => { tail = Buffer.concat([tail, chunk]); consume(); });
    client.on('error', error => finish(false, error.message));
    client.on('timeout', () => finish(false, 'Client idle for 10s'));
    client.on('end', () => { if (sequence <= rounds) finish(false, 'Truncated synthetic exchange'); });
});
function consume() {
    try {
        while (!ended && state !== 'saving' && tail.length >= (state === 'confirm' ? 8 : bytes)) {
            if (state === 'confirm') {
                if (tail.readBigUInt64LE(0) !== BigInt(sequence)) throw Error('Synthetic confirmation differs');
                tail = tail.subarray(8); row.confirmation_ns = now(); rows.push(row); ++sequence;
                state = 'record';
                if (sequence > rounds) { if (tail.length) throw Error('Extra synthetic bytes'); finish(true); return; }
            } else {
                const record = Buffer.from(tail.subarray(0, bytes)); tail = tail.subarray(bytes);
                expected.writeBigUInt64LE(BigInt(sequence), 8);
                if (!record.equals(expected)) throw Error('Synthetic payload/sequence differs');
                row = { sequence, raw_ready_ns: now(), save_begin_ns: now() }; state = 'saving';
                archive.write(record, error => {
                    if (ended) return;
                    if (error) { finish(false, error.message); return; }
                    row.save_end_ns = now(); state = 'confirm'; row.ack_queued_ns = now();
                    const ack = Buffer.alloc(8); ack.writeBigUInt64LE(BigInt(sequence)); const saved = row;
                    socket.write(ack, error => {
                        if (error) finish(false, error.message); else saved.ack_flushed_ns = now();
                    });
                    consume();
                });
            }
        }
    } catch (error) { finish(false, error.message); }
}
function finish(passed, error = null) {
    if (ended) return; ended = true; clearTimeout(deadline);
    server.close(); if (socket) { if (passed) socket.end(); else socket.destroy(); }
    const save = () => {
        const durations = rows.map(r => (Number(BigInt(r.save_end_ns) - BigInt(r.save_begin_ns))) / 1e6);
        const summary = { scope: 'synthetic CPU/network only; no SDK/MMIO/model', passed, error,
            completed: rows.length, expected_rounds: rounds, bytes_per_record: bytes, port: 39481,
            TCP_NODELAY: true, save_ms_mean: durations.length ? durations.reduce((a,b)=>a+b,0)/durations.length : null,
            save_ms_max: durations.length ? Math.max(...durations) : null, automatic_retry: false };
        fs.writeFileSync(path.join(out, 'host-timing.jsonl'), rows.map(r=>JSON.stringify(r)).join('\n')+'\n', {flag:'wx'});
        fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(summary, null, 2)+'\n', {flag:'wx'});
        console.log(JSON.stringify(summary)); process.exitCode = passed ? 0 : 2;
    };
    if (passed) archive.end(save); else { archive.destroy(); save(); }
}
archive.on('error', error => finish(false, error.message));
server.on('error', error => finish(false, error.message));
const deadline = setTimeout(() => finish(false, '90s host deadline'), 90000);
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => finish(false, signal));
server.listen(39481, '127.0.0.1', () => {
    const ready = { ready: true, pid: process.pid, bind: '127.0.0.1:39481', max_seconds: 90,
        scope: 'synthetic only', rounds, bytes_per_record: bytes };
    fs.writeFileSync(path.join(out, 'ready.json'), JSON.stringify(ready), {flag:'wx'});
    console.log('ACK_HOST_READY '+JSON.stringify(ready));
});
