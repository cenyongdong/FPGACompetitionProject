"""Review returned coded prefix and public ioctl overlap, without board execution."""
from pathlib import Path
import collections, hashlib, json
import cv2

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'tools/pose-v1/evidence/producer-vpu-20261011-r2'
P = E / 'on-return/run-on/results'
load = lambda p: [json.loads(x) for x in p.read_text().splitlines()]
events = load(P / 'vpu/encoder/events.jsonl')
obs = load(P / 'vpu-ioctl.jsonl')
packets = load(P / 'vpu/packets.jsonl')
fmt = {x['fourcc']: x for x in events if x['event'] == 'format'}
raw, coded = fmt['NV12']['type'], fmt['H264']['type']
assert (raw, coded) == (10, 9)
assert fmt['NV12']['planes'] == 2 and fmt['H264']['planes'] == 1
sources = [x for x in events if x['event'] == 'source_frame']
queued = [x for x in events if x['event'] == 'input_queued']
captures = [x for x in events if x['event'] == 'capture']
assert len(sources) == len(queued) == 272
assert [x['encoded_id'] for x in sources] == list(range(272))
assert all(not x['inference_result'] for x in sources)
assert len(packets) == len(captures) == 271 and all(x['owned'] for x in packets)
assert [(x['pts_us'], x['bytes']) for x in packets] == [(x['pts_us'], x['bytes']) for x in captures]
video = P / 'vpu/encoder/video.h264'
assert sum(x['bytes'] for x in packets) == video.stat().st_size == 47878
assert all(a['pts_us'] <= b['pts_us'] for a, b in zip(packets, packets[1:]))
q = [x for x in obs if x['request'] == 'QBUF' and x['type'] == raw and x['return'] == 0]
d = [x for x in obs if x['request'] == 'DQBUF' and x['type'] == coded and x['return'] == 0]
assert len(q) == 272 and len(d) == 271
assert [(x['pts_us'], x['bytesused']) for x in d] == [(x['pts_us'], x['bytes']) for x in packets]
assert {x['index'] for x in q} == {0, 1} and {x['index'] for x in d} == {0, 1}
by_pts = {x['pts_us']: x for x in q}
assert len(by_pts) == len(q)
intervals = [(by_pts[x['pts_us']]['begin_ns'], x['end_ns']) for x in d]
rows = []
for i in range(82):
    t = json.loads((P / ('call-' + str(i)) / 'trace.json').read_text())
    for read in t['reads']:
        begin, end = read['copy_begin_ns'], read['copy_end_ns']
        rows.append({'invocation': i, 'value': read.get('value'), 'begin_ns': begin,
                     'end_ns': end, 'submitted_to_capture_overlaps': sum(a < end and begin < b for a, b in intervals)})
cap = cv2.VideoCapture(str(video)); ids = []; frame_hashes = []
while True:
    ok, frame = cap.read()
    if not ok:
        break
    assert frame.shape == (720, 1280, 3)
    ids.append(sum((int(frame[618, 64 + bit * 64].mean()) > 127) << bit for bit in range(10)))
    frame_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
cap.release()
# First coded buffer is a parameter/header packet, not an image.
assert ids == list(range(270))
r = {'status': 'aborted_coded_prefix_verified_not_normal_drain', 'video_sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
     'video_bytes': video.stat().st_size, 'packets': len(packets), 'decoded_images': len(ids),
     'decoded_ids': ids, 'decoded_BGR_sha256': frame_hashes, 'raw_queued': len(q),
     'two_buffers_each_port': True, 'NV12_type': raw, 'H264_type': coded,
     'all_sources_NoInput': True, 'new_pose_throughput': 0, 'packet_PTS_nondecreasing': True,
     'distinct_capture_PTS': len({x['pts_us'] for x in packets}),
     'ioctl_records': len(obs), 'return_errno_counts': {str(k): v for k, v in collections.Counter((x['return'], x['errno_at_return']) for x in obs).items()},
     'copy_spans': rows, 'copy_spans_with_submitted_capture_overlap': sum(x['submitted_to_capture_overlaps'] > 0 for x in rows),
     'overlap_limit': 'Submission-to-capture spans are not hardware busy or DMA fence proof.',
     'normal_LAST_drained': False, 'tail_queued_not_decoded_ids': [270, 271],
     'frozen_summary_zero_counts_limit': 'Abort threw before EncodeResult return; zero submitted/returned fields do not mean no work.'}
(E / 'on.video-review.json').write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\n')
print('270 decoded IDs0..269;271 owned packets;272 raw queued; copy overlaps', r['copy_spans_with_submitted_capture_overlap'], '/164; abort retained')
