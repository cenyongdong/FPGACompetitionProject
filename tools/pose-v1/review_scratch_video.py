"""Decode the isolated synthetic VPU load; never count it as model output."""
import argparse, hashlib, json, re
from pathlib import Path
import cv2
import numpy as np

def rows(p):
    return [json.loads(x) for x in p.read_text().splitlines()]

def nal_types(blob):
    starts = list(re.finditer(b'\x00\x00(?:\x00)?\x01', blob))
    assert starts and starts[0].start() == 0
    return [blob[x.end()] & 31 for x in starts]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('results', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    vpu = a.results / 'vpu'
    summary = json.loads((vpu / 'summary.json').read_text())
    events = rows(vpu / 'encoder/events.jsonl')
    packets = rows(vpu / 'packets.jsonl')
    queued = [x for x in events if x['event'] == 'input_queued']
    captured = [x for x in events if x['event'] == 'capture' and x['bytes']]
    assert summary['drained'] and summary['submitted'] == summary['returned']
    stream = vpu / 'encoder/video.h264'
    raw = stream.read_bytes()
    offset = 0
    image_packets = []
    header_packets = []
    for packet in packets:
        size = packet['bytes']
        if size:
            types = nal_types(raw[offset:offset+size])
            if any(x in (1, 5) for x in types):
                assert sum(x in (1, 5) for x in types) == 1
                image_packets.append(packet)
            else:
                assert all(x in (7, 8) for x in types)
                header_packets.append(packet)
        offset += size
    assert len(queued) == len(image_packets) == summary['submitted']
    assert len(header_packets) == 1 and header_packets[0]['packet'] == 0
    assert packets[-1]['bytes'] == 0 and packets[-1]['pts_us'] == 0
    assert len(packets) == len(image_packets)+2
    assert [x['frame'] for x in queued] == list(range(len(queued)))
    assert [x['pts_us'] for x in queued] == [x['pts_us'] for x in image_packets]
    assert all(x['pts_us'] < y['pts_us'] for x, y in zip(queued, queued[1:]))
    assert [(x['pts_us'], x['bytes']) for x in captured] == [(x['pts_us'], x['bytes']) for x in packets if x['bytes']]
    assert [x['packet'] for x in packets] == list(range(len(packets)))
    assert all(x['owned'] for x in packets)
    assert all(x['capture_ns'] <= y['capture_ns'] for x, y in zip(packets, packets[1:]))
    assert stream.stat().st_size == sum(x['bytes'] for x in packets)
    cap = cv2.VideoCapture(str(stream))
    assert cap.isOpened()
    ids = []
    hashes = []
    while True:
        ok, image = cap.read()
        if not ok:
            break
        assert image.shape == (720, 1280, 3)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        value = 0
        for bit in range(10):
            patch = gray[608:628, 48+bit*64:80+bit*64]
            low, high = int(patch.min()), int(patch.max())
            assert high < 64 or low > 192, (len(ids), bit, low, high)
            value |= (low > 192) << bit
        ids.append(value)
        hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
    cap.release()
    assert ids == list(range(summary['submitted']))
    report = dict(status='synthetic_scratch_VPU_content_and_actual_PTS_passed',
                  decoded_frames=len(ids), encoded_ids=ids, decoded_sha256=hashes,
                  stream_sha256=hashlib.sha256(stream.read_bytes()).hexdigest(),
                  stream_bytes=stream.stat().st_size, actual_PTS_match=True,
                  SPS_PPS_packets=len(header_packets), empty_LAST_packets=1,
                  first_image_capture_ns=image_packets[0]['capture_ns'],
                  last_image_capture_ns=image_packets[-1]['capture_ns'],
                  all_packets_owned=True, SDK_on_encoder_thread=False,
                  NoInput_only=True, model_inference_frames=0,
                  OpenCV_version=cv2.__version__, NumPy_version=np.__version__)
    a.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','decoded_frames','stream_bytes','model_inference_frames')}))

if __name__ == '__main__':
    main()
