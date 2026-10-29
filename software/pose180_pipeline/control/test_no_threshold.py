"""Loopback inference/presentation contract with Top1 and no score cutoff; no SDK."""
import argparse
import json
from pathlib import Path
import signal
import socket
import struct
import subprocess
import time

from test_resident import frame, port


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir()
    ip, raw, status_port, view = [port() for _ in range(4)]
    command = [args.binary, '--output', str(root/'run'), '--session', '123456', '--seconds', '0',
               '--top-k', '1', '--score-threshold', 'none', '--input-port', str(ip),
               '--single-person-stability', '1',
               '--result-port', str(raw), '--status-port', str(status_port), '--view-port', str(view),
               '--mock-delay-ms', '1']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ready = ''
    try:
        ready = process.stdout.readline()
        assert 'mock=1' in ready, ready
        with socket.create_connection(('127.0.0.1', view), 2) as subscriber:
            subscriber.settimeout(2)
            with socket.create_connection(('127.0.0.1', ip), 2) as source:
                for ordinal in range(1, 31):
                    source.sendall(frame(ordinal))
                    time.sleep(.012)
            data = b''
            frames = []
            end = time.monotonic()+3
            while time.monotonic() < end and not any(row['poses'] for row in frames):
                data += subscriber.recv(16384)
                while b'\n' in data:
                    line, data = data.split(b'\n', 1)
                    frames.append(json.loads(line))
            assert frames and any(row['poses'] for row in frames), frames
            assert all(len(row['poses']) <= 1 and len(row['raw_poses']) == 1 for row in frames)
            assert all(row['raw_poses'][0]['candidate'] == 0 for row in frames)  # Equal mock scores.
        with socket.create_connection(('127.0.0.1', status_port), 1) as channel:
            data = b''
            while True:
                chunk = channel.recv(8192)
                if not chunk:
                    break
                data += chunk
        status = json.loads(data)
        assert status['top_k'] == 1 and status['score_threshold'] is None and status['inferred'] >= 10, status
        assert status['single_person_stability'] is True, status
        process.send_signal(signal.SIGTERM)
        out, err = process.communicate(timeout=8)
        completion = json.loads((root/'run/completion.json').read_text())
        assert process.returncode == 0 and completion['native_shutdown_complete'], (out, err)
        # The raw record stores all 180 original scores despite single-person selection.
        record = (root/'run/recent-0.full').read_bytes()
        assert len(record) > 0 and len(record) % 74544 == 0
        for offset in range(0, len(record), 74544):
            assert struct.unpack_from('<180f', record, offset+43584) == (.5,)*180
        assert all(row['top_k']==1 and row['score_threshold'] is None for row in frames)
        (root/'stdout.log').write_text(ready+out)
        (root/'stderr.log').write_text(err)
        (root/'result.json').write_text(json.dumps(dict(mock=True, top_k=1, score_threshold=None,
            frames_observed=len(frames), maximum_displayed_people=max(len(row['poses']) for row in frames),
            raw_archive_bytes=len(record), final=status, native_shutdown_complete=True, native_exit=0), indent=2))
        print('TOP1_NO_THRESHOLD_PASS inferred=%d view_frames=%d' % (status['inferred'], len(frames)))
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=8)


if __name__ == '__main__':
    main()
