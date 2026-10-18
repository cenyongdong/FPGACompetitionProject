// 只读导入旧演示实际保存的selected_pose；不推理、不更改来源。
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { HERE, WORK, CLIP } from '../paths.mjs';
import { BONES, encodeFrame } from '../protocol.mjs';

const need = (ok, why) => { if (!ok) throw new Error(why); };
const hash = b => createHash('sha256').update(b).digest('hex');
const destination = path.join(HERE, 'data/demo60.json');
const previous = fs.existsSync(destination) ? JSON.parse(fs.readFileSync(destination)) : null;
const source = process.argv[2] || previous?.source_evidence;
need(CLIP === 'demo60', 'prepare-demo requires POSE_CLIP=demo60');
need(source, 'Supply the saved demo-20261011-r4 evidence directory');
const evidence = fs.realpathSync(source);
const read = file => fs.readFileSync(path.join(evidence, file), 'utf8');
// u64身份在JSON解析前转为字符串，避免Number精度丢失。
const parse = text => JSON.parse(text.replace(/("(?:frame_id|invocation|source_time_ns)"\s*:\s*)(\d+)/g, '$1"$2"'));
const sourceFile = 'demo-return/run-demo/results/results/frames.jsonl';
const sourceText = read(sourceFile);
const rows = sourceText.trim().split(/\r?\n/).map(parse);
const catalog = JSON.parse(read('demo-host/inputs/catalog.json'));
const sent = parse(read('demo-host/sent.json'));
const review = JSON.parse(read('demo.review.json'));
const summary = JSON.parse(read('demo-return/run-demo/results/summary.json'));
need(review.input_windows === 60 && review.different_pose_outputs === 60 && summary.completed === 60 && !summary.failed, 'Original successful run evidence differs');
need(rows.length === 60 && catalog.length === 60 && sent.records.length === 60, 'Incomplete archive');
const records = [], frames = [], segments = [];
const uniquePose = new Set(), uniqueInput = new Set();
const firstTime = BigInt(rows[0].source_time_ns);
rows.forEach((row, i) => {
    const input = catalog[i], transmission = sent.records[i];
    need(row.frame_id === String(input.frame_id) && row.frame_id === transmission.frame_id, 'Frame/source identity differs');
    need(row.invocation === String(i) && input.sequence === i, 'Original order differs');
    need(row.source_time_ns === transmission.source_time_ns, 'Source clock differs from archived sender');
    need(transmission.payload_sha256 === input.payload_sha256, 'Input provenance differs');
    need(i === 0 || BigInt(row.source_time_ns) > BigInt(rows[i - 1].source_time_ns), 'Source clock did not advance');
    need(Number.isInteger(row.best_slot) && row.best_slot >= 0 && row.best_slot < 100, 'Invalid original candidate');
    need(row.selected_pose?.length === 42 && row.selected_pose.every(v => Number.isFinite(v) && Math.fround(v) === v), 'Selected output is not exact finite FP32');
    need(Number.isFinite(row.best_score) && Math.fround(row.best_score) === row.best_score, 'Invalid original FP32 score');
    const name = path.win32.basename(input.source_file, '.mat');
    const match = name.match(/^(.*)_(\d+)$/);
    need(match, 'Source sample name has no sequence index');
    const prefix = match[1], sample = Number(match[2]);
    let segment = segments.at(-1);
    if (!segment || segment.id !== prefix || segment.last_sample + 1 !== sample) {
        segment = { id: prefix, start: i, end: i, first_sample: sample, last_sample: sample };
        segments.push(segment);
    }
    segment.end = i;
    segment.last_sample = sample;
    const frame = { session: '2026101802', frame: row.frame_id, invocation: row.invocation,
        source_ns: row.source_time_ns, published_ns: '0', sequence: String(i + 1),
        candidate: row.best_slot, score: row.best_score, flags: 1, joints: row.selected_pose };
    const bytes = encodeFrame(frame);
    records.push(bytes);
    uniquePose.add(hash(bytes.subarray(88)));
    uniqueInput.add(input.payload_sha256);
    frames.push({ case: name, frame: frame.frame, invocation: frame.invocation, sequence: frame.sequence,
        candidate: frame.candidate, score: frame.score, source_ns: frame.source_ns,
        playback_ms: Number(BigInt(frame.source_ns) - firstTime) / 1e6,
        segment_id: prefix, sample, process_ms: row.process_ms,
        source_record: sourceFile + ':line ' + (i + 1),
        input_payload_sha256: input.payload_sha256, record_sha256: hash(bytes) });
});
need(uniquePose.size === 60 && uniqueInput.size === 60, 'Repeated fixtures are not a continuous action archive');
for (const s of segments) {
    s.frames = s.end - s.start + 1;
    s.duration_ms = frames[s.end].playback_ms - frames[s.start].playback_ms;
}
const packed = Buffer.concat(records);
const manifest = { schema: 'PIWPOSE1/1', source: 'archived_real_board_output', fresh_inferences: 0,
    title: '原演示连续动作', model: '2026-10-11 original accepted PS/NPU model',
    model_graph_sha256: '75ffdc37b93dcb4913678991d6e7cf5cd0ab09c59653224d07c7434345acb8a0',
    model_raw_sha256: '3991a679282a4c6b014aece59b717910bc53fd14e67c0fac5fb9f93d4ae054d3',
    model_label: '原演示模型 · 2026-10-11', source_evidence: evidence,
    source_record_file: sourceFile, source_record_sha256: hash(Buffer.from(sourceText)),
    source_report: 'demo.review.json', source_representation: 'original full-precision JSON selected_pose and best_score',
    numeric_scope: 'first 3 archived reference checks; remaining 57 archived shape/finite/selection/mapping checks only; no new accuracy claim',
    timing: 'original host send intervals, same clock; not RF sample rate or cross-host latency',
    coordinate_space: 'model C0/C1/C2; no room calibration', topology: 'project-14-v1', bones: BONES,
    default_playback_hz: sent.hz, segments, default_segment: segments.reduce((a,b) => b.frames > a.frames ? b : a).id,
    unique_selected_poses: uniquePose.size, unique_inputs: uniqueInput.size,
    frames, records_sha256: hash(packed) };
fs.mkdirSync(WORK, { recursive: true });
fs.mkdirSync(path.dirname(destination), { recursive: true });
fs.writeFileSync(path.join(WORK, 'records.piwpose'), packed);
fs.writeFileSync(destination, JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ prepared: frames.length, bytes: packed.length, unique_poses: uniquePose.size,
    segments, source_representation: manifest.source_representation, work: WORK }, null, 2));
