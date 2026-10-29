export const VIEW_LIMIT = 16384;

export function decodePresentation(line) {
	if (Buffer.byteLength(line) > VIEW_LIMIT)
		throw new Error('Oversize presentation');
	const f = JSON.parse(line),
		  id = x => typeof x === 'string' && /^\d{1,20}$/.test(x) && BigInt(x) <= 18446744073709551615n;
	if (f.schema !== 'PIWVIEW1' || f.version !== 1 || typeof f.replay !== 'boolean' ||
		!['session', 'frame', 'sequence', 'source_ns'].every(k => id(f[k])) || f.session === '0' ||
		f.sequence === '0' || f.hold_ms !== 250)
		throw new Error('Invalid presentation identity');

	// Older recordings used Top3/>0.2. New records explicitly carry their policy;
	// null disables the cutoff while preserving finite-value validation.
	const topK = Object.hasOwn(f, 'top_k') ? f.top_k : 3;
	const threshold = Object.hasOwn(f, 'score_threshold') ? f.score_threshold : .2;
	if (!Number.isInteger(topK) || topK < 1 || topK > 3 ||
		(threshold !== null && (!Number.isFinite(threshold) || threshold < 0 || threshold > 1)))
		throw new Error('Invalid presentation selection');

	// 原始候选和展示姿态都验证有限数值；只有展示姿态要求唯一的有效跟踪 ID。
	for (const field of ['poses', 'raw_poses']) {
		if (!Array.isArray(f[field]) || f[field].length > topK)
			throw new Error('Invalid presentation count');
		const ids = new Set();
		for (const p of f[field]) {
			if (!id(p.track) || !id(p.observed_ns) || BigInt(p.observed_ns) > BigInt(f.source_ns) ||
				!Number.isInteger(p.candidate) || p.candidate < 0 || p.candidate >= 180 ||
				!Number.isFinite(p.score) || (threshold !== null && !(p.score > Math.fround(threshold))) ||
				typeof p.held !== 'boolean' || !Number.isFinite(p.age_ms) || p.age_ms < 0 || p.age_ms > 250 ||
				!Array.isArray(p.joints) || p.joints.length !== 42 || !p.joints.every(Number.isFinite))
				throw new Error('Invalid presentation person');
			if (field === 'poses') {
				if (p.track === '0' || ids.has(p.track))
					throw new Error('Invalid track identity');
				ids.add(p.track);
			}
			if (Math.abs(p.age_ms - Number(BigInt(f.source_ns) - BigInt(p.observed_ns)) / 1e6) > 0.001)
				throw new Error('Inconsistent observation age');
			if (!p.held && p.observed_ns !== f.source_ns)
				throw new Error('Current pose has old observation');
		}
	}
	return f;
}

export class PresentationReader {
	pending = '';

	push(chunk, accept) {
		// ASCII numeric JSON only; no unbounded accumulation on missing newline.
		let offset = 0;
		while (offset < chunk.length) {
			const end = chunk.indexOf(10, offset), stop = end < 0 ? chunk.length : end;
			if (this.pending.length + stop - offset > VIEW_LIMIT)
				throw new Error('Oversize presentation stream');
			this.pending += chunk.toString('utf8', offset, stop);
			offset = end < 0 ? chunk.length : end + 1;
			if (end >= 0) {
				const f = decodePresentation(this.pending);
				this.pending = '';
				accept(f);
			}
		}
	}

	reset() {
		this.pending = '';
	}
}

export function visiblePresentation(frame, ageMs) {
	// 本地显示年龄叠加板端保持时间，断流后不继续展示过期骨架。
	return {
		...frame,
		poses : frame.poses.filter(p => p.age_ms + ageMs <= frame.hold_ms),
		raw_poses : frame.raw_poses.filter(p => p.age_ms + ageMs <= frame.hold_ms)
	};
}
