import { EventEmitter } from 'node:events';

export class CreditWindow extends EventEmitter {
    constructor(limit = 8, maxAgeMs = 1000, clock = () => process.hrtime.bigint()) {
        super();
        if (!Number.isInteger(limit) || limit < 1 || limit > 64 || !Number.isFinite(maxAgeMs) || maxAgeMs <= 0 || maxAgeMs > 60000) throw new Error('Invalid credit/age bound');
        this.limit = limit; this.maxAgeNs = BigInt(Math.round(maxAgeMs * 1e6)); this.clock = clock;
        this.pending = new Map(); this.sent = 0; this.confirmed = 0; this.high = 0; this.closed = null; this.waits = 0;
    }
    checkAge() {
        const first = this.pending.values().next().value;
        if (first !== undefined && this.clock() - first > this.maxAgeNs) throw new Error('Oldest unconfirmed frame exceeded age budget');
    }
    async wait() {
        while (this.pending.size >= this.limit) {
            if (this.closed) throw this.closed;
            this.checkAge(); ++this.waits;
            const first = this.pending.values().next().value;
            const remaining = Math.max(1, Number(this.maxAgeNs - (this.clock() - first)) / 1e6);
            await new Promise((resolve,reject) => {
                const changed = () => { clearTimeout(timer); this.off('changed',changed); this.closed ? reject(this.closed) : resolve(); };
                const timer = setTimeout(changed, Math.min(remaining + 1,100)); this.once('changed',changed);
            });
        }
        if (this.closed) throw this.closed;
        this.checkAge();
    }
    reserve(index, stamp) {
        if (this.closed) throw this.closed;
        this.checkAge();
        if (index !== this.sent || this.pending.size >= this.limit) throw new Error('Input credit bound/sequence exceeded');
        this.pending.set(index,stamp); ++this.sent; this.high = Math.max(this.high,this.pending.size);
    }
    confirm(index) {
        this.checkAge();
        if (index !== this.confirmed || !this.pending.delete(index)) throw new Error('Confirmation credit identity mismatch');
        ++this.confirmed; this.emit('changed');
    }
    close(error = new Error('Input credit closed')) { this.closed ??= error; this.emit('changed'); }
}

// The caller must await each operation: no unbounded application write queue.
// A write owns its Buffer until callback AND (if necessary) drain have occurred.
export class BoundedWriter {
    constructor(stream, maxBytes) { this.stream = stream; this.maxBytes = maxBytes; this.busy = false; this.bytes = 0; this.high = 0; this.failure = null; stream.on('error',error => { this.failure = error; }); }
    async write(bytes) {
        if (this.busy || bytes.length > this.maxBytes) throw new Error('Archive/write concurrency or byte bound exceeded');
        if (this.failure || this.stream.destroyed || this.stream.writableEnded) throw this.failure || new Error('Write stream closed');
        this.busy = true; this.bytes = bytes.length; this.high = Math.max(this.high,this.bytes);
        try {
            await new Promise((resolve,reject) => {
                let accepted = null, callbackDone = false, drained = false, settled = false;
                const cleanup = () => { this.stream.off('error',bad); this.stream.off('close',closed); this.stream.off('drain',drain); };
                const bad = error => { if (settled) return; settled = true; cleanup(); reject(error); };
                const closed = () => bad(new Error('Write stream closed before completion'));
                const done = () => { if (!settled && callbackDone && accepted !== null && (accepted || drained)) { settled = true; cleanup(); resolve(); } };
                const drain = () => { drained = true; done(); };
                this.stream.once('error',bad); this.stream.once('close',closed); this.stream.once('drain',drain);
                try { accepted = this.stream.write(bytes,error => { if (error) bad(error); else { callbackDone = true; done(); } }); done(); } catch (error) { bad(error); }
            });
        } finally { this.bytes = 0; this.busy = false; }
    }
    async end() {
        if (this.busy) throw new Error('Cannot end writer while a buffer is owned');
        if (this.stream.destroyed || this.stream.writableFinished) return;
        await new Promise((resolve,reject) => {
            const bad = error => { cleanup(); reject(error); };
            const cleanup = () => { this.stream.off('error',bad); this.stream.off('close',closed); };
            const closed = () => { cleanup(); this.stream.writableFinished ? resolve() : reject(new Error('Archive closed before finish')); };
            this.stream.once('error',bad); this.stream.once('close',closed); this.stream.end(() => { cleanup(); resolve(); });
        });
    }
}

export class BufferPool {
    constructor(count, bytes) { this.free = Array.from({length:count},() => Buffer.alloc(bytes)); this.owned = new Set(); }
    acquire() { const buffer = this.free.pop(); if (!buffer) throw new Error('Fixed buffer pool exhausted'); this.owned.add(buffer); return buffer; }
    release(buffer) { if (!this.owned.delete(buffer)) throw new Error('Buffer ownership mismatch'); this.free.push(buffer); }
}

export class SendSchedule {
    constructor(hz, toleranceMs = 20) {
        this.period = BigInt(Math.round(1e9 / hz)); this.tolerance = BigInt(Math.round(toleranceMs * 1e6));
        this.epoch = null; this.previous = null; this.strict = true; this.missed = 0; this.pauses = 0; this.lateness = [];
    }
    planned(index) { if (this.epoch === null) throw new Error('Pacing epoch absent'); return this.epoch + BigInt(index) * this.period; }
    earliest(index) {
        const planned = this.planned(index);
        // Ordinary dispatch jitter follows the original absolute slots. Only a
        // whole expired slot switches continuation to non-burst backpressure.
        return this.previous !== null && this.previous >= planned ? this.previous + this.period : planned;
    }
    mark(index, stamp) {
        const late = Number(stamp - this.planned(index)) / 1e6; this.lateness.push(late);
        if (stamp > this.planned(index) + this.tolerance || stamp < this.planned(index) - this.tolerance) { this.strict = false; ++this.missed; }
        if (this.previous !== null && stamp - this.previous > this.period + this.tolerance) { this.strict = false; ++this.pauses; }
        if (this.previous !== null && this.previous >= this.planned(index) && stamp < this.previous + this.period - 1000000n) throw new Error('Catch-up burst prohibited');
        this.previous = stamp; return late;
    }
}
