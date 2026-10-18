export const RECORD_BYTES = 256;
export const MAGIC = 'PIWPOSE1';
export const BONES = [[0,1],[0,2],[0,3],[2,4],[2,5],[3,6],[3,7],[4,8],[5,7],[5,9],[6,10],[7,11],[9,12],[11,13]];
const need = (x, message) => { if (!x) throw new Error(message); };

export function encodeFrame(f) {
    const b = Buffer.alloc(RECORD_BYTES);
    b.write(MAGIC); b.writeUInt16LE(1, 8); b.writeUInt16LE(88, 10); b.writeUInt32LE(RECORD_BYTES, 12);
    for (const [off, field] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[48,'published_ns'],[80,'sequence']]) {
        b.writeBigUInt64LE(BigInt(f[field] ?? 0), off);
    }
    b.writeUInt32LE(f.candidate, 56); b.writeUInt16LE(14, 60); b.writeUInt16LE(f.flags ?? 1, 62);
    b.writeFloatLE(f.score, 64); b.writeUInt32LE(1, 68); b.writeUInt32LE(1, 72);
    need(f.joints?.length === 42, 'Expected 42 coordinates');
    f.joints.forEach((x, i) => b.writeFloatLE(x, 88 + 4 * i));
    decodeFrame(b);
    return b;
}

export function decodeFrame(b) {
    need(b.length === RECORD_BYTES && b.toString('ascii', 0, 8) === MAGIC, 'Invalid record size or magic');
    need(b.readUInt16LE(8) === 1 && b.readUInt16LE(10) === 88 && b.readUInt32LE(12) === RECORD_BYTES, 'Unsupported version or layout');
    need(b.readUInt16LE(60) === 14 && b.readUInt16LE(62) <= 1, 'Invalid joint count or flags');
    need(b.readUInt32LE(68) === 1 && b.readUInt32LE(72) === 1 && b.readUInt32LE(76) === 0, 'Unsupported coordinates or topology');
    const f = { kind: 'pose', schema: 'PIWPOSE1/1', joints: [] };
    for (const [off, field] of [[16,'session'],[24,'frame'],[32,'invocation'],[40,'source_ns'],[48,'published_ns'],[80,'sequence']]) {
        f[field] = b.readBigUInt64LE(off).toString();
    }
    f.candidate = b.readUInt32LE(56); f.flags = b.readUInt16LE(62); f.score = b.readFloatLE(64);
    for (let i = 0; i < 42; ++i) f.joints.push(b.readFloatLE(88 + 4 * i));
    need(f.session !== '0' && f.sequence !== '0' && f.candidate < 100, 'Invalid session, sequence or candidate');
    need(Number.isFinite(f.score) && f.joints.every(Number.isFinite), 'Non-finite model output');
    f.source = f.flags === 1 ? 'archived_real_board_output' : 'live_board_output';
    return f;
}

// 固定记录流：只保留不足一帧的尾部；分包/合包都不改变记录边界。
export class RecordStream {
    #tail = Buffer.alloc(0);
    #sequence = 0n;
    #session = null;
    push(chunk) {
        const b = this.#tail.length ? Buffer.concat([this.#tail, chunk]) : chunk;
        const frames = [];
        let offset = 0;
        while (b.length - offset >= RECORD_BYTES) {
            const bytes = Buffer.from(b.subarray(offset, offset + RECORD_BYTES));
            const frame = decodeFrame(bytes);
            need(this.#session === null || frame.session === this.#session, 'Session changed inside TCP connection');
            need(BigInt(frame.sequence) === this.#sequence + 1n, 'Missing, repeated or reordered record');
            this.#session = frame.session; this.#sequence = BigInt(frame.sequence);
            frames.push({ frame, bytes }); offset += RECORD_BYTES;
        }
        this.#tail = Buffer.from(b.subarray(offset));
        return frames;
    }
    finish() { need(this.#tail.length === 0, 'Truncated TCP record at EOF'); }
}
