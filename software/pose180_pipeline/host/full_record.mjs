// PIWFUL3 keeps the selected 256-byte PIWPOSE1 envelope and owns all 180 outputs.
export const FULL_BYTES = 74544;
export const INPUT_BYTES = 43200;
export const CANDIDATES = 180;
export const SCORE_OFFSET = 384 + INPUT_BYTES;
export const POSE_OFFSET = SCORE_OFFSET + CANDIDATES * 4;
const need = (ok, text) => { if (!ok) throw new Error(text); };

export function decodeFrame(b) {
    need(b.length === 256 && b.toString('ascii', 0, 8) === 'PIWPOSE1', 'Invalid selected pose envelope');
    need(b.readUInt16LE(8) === 1 && b.readUInt16LE(10) === 88 && b.readUInt32LE(12) === 256, 'Unsupported selected pose layout');
    need(b.readUInt16LE(60) === 14 && b.readUInt16LE(62) === 0, 'Expected 14-joint live pose');
    need(b.readUInt32LE(68) === 1 && b.readUInt32LE(72) === 1 && b.readUInt32LE(76) === 0, 'Unsupported coordinates or topology');
    const frame = { kind: 'pose', schema: 'PIWPOSE1/1', source: 'live_board_output', joints: [] };
    for (const [offset, name] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[48,'published_ns'],[80,'sequence']]) frame[name] = b.readBigUInt64LE(offset).toString();
    frame.candidate = b.readUInt32LE(56); frame.flags = b.readUInt16LE(62); frame.score = b.readFloatLE(64);
    for (let i = 0; i < 42; ++i) frame.joints.push(b.readFloatLE(88 + i * 4));
    need(frame.session !== '0' && frame.sequence !== '0' && frame.candidate < CANDIDATES, 'Invalid session, sequence or candidate');
    need(Number.isFinite(frame.score) && frame.joints.every(Number.isFinite), 'Non-finite selected pose');
    return frame;
}

// Call only AFTER the complete raw record has reached the archive write callback.
export function decodeFull(b) {
    need(b.length === FULL_BYTES && b.toString('ascii',0,8) === 'PIWFUL3\0' && b.readUInt32LE(8) === 3 && b.readUInt32LE(12) === FULL_BYTES, 'Invalid PIWFUL3 complete-result record');
    const frame = decodeFrame(b.subarray(128,384));
    for (const [offset,name] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[72,'sequence']]) need(b.readBigUInt64LE(offset).toString() === frame[name], 'Full/pose identity mismatch');
    need(b.readUInt32LE(124) === 0, 'Expected live complete result');
    const metrics = {};
    for (const [offset,name] of [[80,'process_ms'],[88,'preprocess_ms'],[96,'forward_ms'],[104,'output_ms']]) {
        metrics[name] = b.readDoubleLE(offset);
        need(Number.isFinite(metrics[name]) && metrics[name] >= 0, 'Invalid processing time');
    }
    const arrived = b.readBigUInt64LE(48), began = b.readBigUInt64LE(56), returned = b.readBigUInt64LE(64);
    need(arrived <= began && began <= returned, 'Invalid board timeline');
    metrics.queue_ms = Number(began - arrived) / 1e6;
    metrics.input_queue_high = b.readUInt32LE(112); metrics.candidate_count = b.readUInt32LE(116);
    need(metrics.candidate_count === CANDIDATES, 'Unexpected complete-result candidate count');
    for (let offset = 384; offset < FULL_BYTES; offset += 4) need(Number.isFinite(b.readFloatLE(offset)), 'Non-finite complete model result');
    let best = 0;
    for (let i = 1; i < CANDIDATES; ++i) if (b.readFloatLE(SCORE_OFFSET + i * 4) > b.readFloatLE(SCORE_OFFSET + best * 4)) best = i;
    need(frame.candidate === best && b.readUInt32LE(120) === best && frame.score === b.readFloatLE(SCORE_OFFSET + best * 4), 'Selection mismatch');
    frame.joints.forEach((value,i) => need(value === b.readFloatLE(POSE_OFFSET + (best * 42 + i) * 4), 'Selected/full pose mismatch'));
    return { ...frame, metrics };
}

// One reusable full record and one confirmation word. Awaited consumers retain
// ownership until archive/ACK processing finishes, including arbitrary TCP splits.
export class ConfirmedReader {
    raw = Buffer.alloc(FULL_BYTES);
    confirmation = Buffer.alloc(8);
    used = 0;
    pending = false;
    async push(chunk, onRaw, onConfirmed) {
        let offset = 0;
        while (offset < chunk.length) {
            const target = this.pending ? this.confirmation : this.raw;
            const take = Math.min(target.length - this.used, chunk.length - offset);
            chunk.copy(target, this.used, offset, offset + take); this.used += take; offset += take;
            if (this.used !== target.length) continue;
            this.used = 0;
            if (this.pending) { await onConfirmed(target.readBigUInt64LE()); this.pending = false; }
            else { this.pending = true; await onRaw(target); }
        }
    }
    partial() { return this.used ? Buffer.from((this.pending ? this.confirmation : this.raw).subarray(0,this.used)) : Buffer.alloc(0); }
    finish() { need(!this.used && !this.pending, 'Truncated or unconfirmed complete result at EOF'); }
}
