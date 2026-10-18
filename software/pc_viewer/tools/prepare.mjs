import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { ROOT, HERE, WORK } from '../paths.mjs';
import { BONES, encodeFrame } from '../protocol.mjs';

const relative = 'tools/pose-v1/evidence/shared-stability-20261015-r2/returned-basic/run-basic/results';
const dir = path.join(ROOT, relative);
const hdmi = path.join(ROOT, 'tools/pose-v1/evidence/hdmi-display-20261017-r1');
const rows = fs.readFileSync(path.join(dir, 'frames.jsonl'), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
const displayed = fs.readFileSync(path.join(hdmi, 'returned-render/saved-skeleton/frames.jsonl'), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
const hash = b => createHash('sha256').update(b).digest('hex');
if (rows.length !== 3 || displayed.length !== 3) throw new Error('Expected the three archived accepted board results');
const records = [], frames = [];
rows.forEach((row, i) => {
    if (!row.matched || !row.finite || !row.scores_bitwise_equal || row.frame_id !== displayed[i].frame_id) throw new Error('Archived gate/source mismatch');
    const source = path.join(dir, 'frame-' + i);
    const scores = fs.readFileSync(path.join(source, 'scores.f32'));
    const poses = fs.readFileSync(path.join(source, 'poses.f32'));
    if (scores.length !== 400 || poses.length !== 16800) throw new Error('Full archived output shape differs');
    for (const b of [scores, poses]) for (let off = 0; off < b.length; off += 4) {
        if (!Number.isFinite(b.readFloatLE(off))) throw new Error('Non-finite archived output');
    }
    // 复用已验收显示记录的候选选择；不新增置信阈值或人数判定。
    const candidate = displayed[i].selected_candidate;
    if (!Number.isInteger(candidate) || candidate < 0 || candidate >= 100) throw new Error('Invalid archived candidate');
    const score = scores.readFloatLE(candidate * 4);
    for (let n = 0; n < 100; ++n) {
        const other = scores.readFloatLE(n * 4);
        if (other > score || (n < candidate && other === score)) throw new Error('Archived highest-score policy mismatch');
    }
    for (const [name, bytes] of [['scores.f32', scores], ['poses.f32', poses]]) {
        const paired = fs.readFileSync(path.join(hdmi, 'build-saved-r1/package/frame-' + i, name));
        if (!paired.equals(bytes)) throw new Error('HDMI archive and original board output differ');
    }
    const joints = Array.from({ length: 42 }, (_, j) => poses.readFloatLE(candidate * 168 + j * 4));
    const frame = { session: '2026101801', frame: String(row.frame_id), invocation: String(row.invocation),
        source_ns: '0', published_ns: '0', sequence: String(i + 1), candidate, score, flags: 1, joints };
    const bytes = encodeFrame(frame);
    if (!bytes.subarray(88).equals(poses.subarray(candidate * 168, candidate * 168 + 168))) throw new Error('Coordinate bytes changed');
    records.push(bytes);
    frames.push({ case: row.case, frame: frame.frame, invocation: frame.invocation, sequence: frame.sequence,
        candidate, score, process_ms: row.process_ms, checked_joint_delta_mm: row.max_checked_joint_delta_mm,
        source_directory: relative + '/frame-' + i, scores_sha256: hash(scores), poses_sha256: hash(poses),
        record_sha256: hash(bytes) });
});
const packed = Buffer.concat(records);
const manifest = { schema: 'PIWPOSE1/1', source: 'archived_real_board_output', fresh_inferences: 0,
    model: 'fixed shared FP16 graph, ADR_48 v2', original_capture_time: 'not supplied by archive',
    coordinate_space: 'model C0/C1/C2; no room calibration', topology: 'project-14-v1', bones: BONES,
    default_playback_hz: 2, frames, records_sha256: hash(packed),
    source_report: 'tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md' };
fs.mkdirSync(WORK, { recursive: true });
fs.mkdirSync(path.join(HERE, 'data'), { recursive: true });
fs.writeFileSync(path.join(WORK, 'records.piwpose'), packed);
fs.writeFileSync(path.join(HERE, 'data/archive.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ prepared: frames.length, bytes: packed.length, fresh_inferences: 0, work: WORK }));
