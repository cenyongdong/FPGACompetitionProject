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

// Presentation only: retain the validated original envelope and raw archive.
// Float32 threshold matches the board's strict comparison with 0.2f.
export function selectTopPoses(b, topK=3, threshold=0.2) {
    need(Number.isInteger(topK)&&topK>0&&topK<=3&&Number.isFinite(threshold),'Invalid display selection');
    const ranked=Array.from({length:CANDIDATES},(_,candidate)=>({candidate,score:b.readFloatLE(SCORE_OFFSET+candidate*4)}));
    need(ranked.every(p=>Number.isFinite(p.score)),'Non-finite display score');
    ranked.sort((a,b)=>b.score-a.score||a.candidate-b.candidate);
    return ranked.slice(0,topK).filter(p=>p.score>Math.fround(threshold)).map(p=>({...p,
        joints:Array.from({length:42},(_,i)=>b.readFloatLE(POSE_OFFSET+(p.candidate*42+i)*4))}));
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

// Optional telemetry subscriber: one fixed record buffer, no ACK or raw archive.
// onRecord receives an owned decoded object; it never retains the reusable bytes.
export class FullRecordReader {
    raw = Buffer.alloc(FULL_BYTES);
    used = 0;
    push(chunk, onRecord) {
        need(Buffer.isBuffer(chunk) && typeof onRecord === 'function', 'Expected buffer and record callback');
        for (let offset = 0; offset < chunk.length;) {
            const length = Math.min(FULL_BYTES - this.used, chunk.length - offset);
            chunk.copy(this.raw, this.used, offset, offset + length);
            this.used += length; offset += length;
            if (this.used !== FULL_BYTES) continue;
            this.used = 0;
            onRecord(decodeFull(this.raw));
        }
    }
    reset() { this.used = 0; }
}

// Only actual process_ms observations whose complete identities also arrived on
// the selected presentation stream enter these statistics. Clocks below are PC
// monotonic receipt times, not cross-device capture-to-display latency.
export class ProcessingWindow {
    constructor({windowMs = 5000, maxRecords = 256} = {}) {
        need(Number.isFinite(windowMs) && windowMs > 0 && windowMs <= 5000,
            'Processing window must be bounded to 5000 ms');
        need(Number.isInteger(maxRecords) && maxRecords > 0 && maxRecords <= 256,
            'Processing cache must be bounded to 256 records');
        this.windowMs = windowMs; this.maxRecords = maxRecords;
        this.reset();
    }
    reset() {
        this.session = null; this.viewSequence = 0n;
        this.records = new Map(); this.resultSequences = new Map();
        this.retiredSessions = new Set();
    }
    identity(frame) {
        const values = ['session','sequence','frame','source_ns'].map(name => frame?.[name]);
        if (!values.every(value => typeof value === 'string' && /^\d{1,20}$/.test(value))) return null;
        const numbers = values.map(BigInt);
        if (numbers.some(value => value > 18446744073709551615n) || numbers[0] === 0n || numbers[1] === 0n) return null;
        const [session, sequence, sourceFrame, sourceNs] = numbers.map(String);
        return {session, sequence: numbers[1], key: [session,sequence,sourceFrame,sourceNs].join(':')};
    }
    prune(nowMs) {
        need(Number.isFinite(nowMs) && nowMs >= 0, 'Expected a finite monotonic receipt time');
        for (const [key, entry] of this.records) {
            const at = entry.viewAt ?? entry.resultAt;
            if (nowMs - at >= this.windowMs) this.records.delete(key);
        }
    }
    trim() {
        while (this.records.size > this.maxRecords) this.records.delete(this.records.keys().next().value);
        while (this.resultSequences.size > this.maxRecords) this.resultSequences.delete(this.resultSequences.keys().next().value);
        while (this.retiredSessions.size > this.maxRecords) this.retiredSessions.delete(this.retiredSessions.values().next().value);
    }
    observeResult(frame, nowMs) {
        this.prune(nowMs);
        const id = this.identity(frame), processMs = frame?.metrics?.process_ms;
        if (!id || !Number.isFinite(processMs) || processMs < 0 || this.retiredSessions.has(id.session)) return false;
        // A TCP result stream is ordered. Watermarks prevent retransmitted or
        // expired identities from becoming fresh samples after cache eviction.
        if (id.sequence <= (this.resultSequences.get(id.session) ?? 0n)) return false;
        this.resultSequences.delete(id.session); this.resultSequences.set(id.session, id.sequence);
        let entry = this.records.get(id.key);
        if (!entry && id.session === this.session && id.sequence <= this.viewSequence) { this.trim(); return false; }
        if (!entry) { entry = {session: id.session}; this.records.set(id.key, entry); }
        entry.resultAt = nowMs; entry.processMs = processMs;
        this.trim(); return true;
    }
    observeView(frame, nowMs) {
        this.prune(nowMs);
        const id = this.identity(frame);
        if (!id || this.retiredSessions.has(id.session)) return false;
        if (id.session !== this.session) {
            if (this.session !== null) this.retiredSessions.add(this.session);
            this.session = id.session; this.viewSequence = 0n;
            // Retain telemetry which arrived ahead of this new view session.
            for (const [key, entry] of this.records) if (entry.session !== this.session) this.records.delete(key);
        }
        if (id.sequence <= this.viewSequence) { this.trim(); return false; }
        this.viewSequence = id.sequence;
        let entry = this.records.get(id.key);
        if (!entry) { entry = {session: id.session}; this.records.set(id.key, entry); }
        entry.viewAt = nowMs;
        this.trim(); return true;
    }
    snapshot(nowMs) {
        this.prune(nowMs);
        const values = [];
        for (const entry of this.records.values()) {
            if (entry.session === this.session && entry.viewAt !== undefined &&
                nowMs >= entry.viewAt && Number.isFinite(entry.processMs)) values.push(entry.processMs);
        }
        values.sort((a,b) => a-b);
        const count = values.length, middle = Math.floor(count / 2);
        // Median averages the middle pair; P95 uses the nearest-rank definition.
        return {session: this.session, samples: count,
            median_ms: count ? (count % 2 ? values[middle] : (values[middle-1] + values[middle]) / 2) : null,
            p95_ms: count ? values[Math.ceil(.95 * count) - 1] : null};
    }
}
