"""Synthetic CPU/network only: no SDK, MMIO, model, BOOT or listener."""
import argparse, json, socket, statistics, struct, time
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path, help='Fresh directory; parent must exist')
    args = p.parse_args(); args.output.mkdir()
    started = time.monotonic(); end = started + 15; rows = []; error = None; connection = None
    payload = bytearray(b'\xa5' * 60784); period = round(1e9/30)
    def remaining():
        value = end-time.monotonic()
        if value <= 0: raise TimeoutError('15s client deadline')
        return min(value, 3.0)
    def exact(count):
        data = bytearray()
        while len(data) < count:
            connection.settimeout(remaining()); chunk = connection.recv(count-len(data))
            if not chunk: raise RuntimeError('Synthetic ACK truncated')
            data.extend(chunk)
        return data
    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        connection.settimeout(remaining()); connection.connect(('127.0.0.1',39481))
        next_send = time.monotonic_ns()
        for sequence in range(1,65):
            delay = (next_send-time.monotonic_ns())/1e9
            if delay > 0: time.sleep(min(delay, remaining()))
            struct.pack_into('<8sQ', payload, 0, b'SYNTHACK', sequence)  # Ordinary CPU memory only.
            send_begin = time.monotonic_ns(); connection.settimeout(remaining()); connection.sendall(payload)
            send_end = time.monotonic_ns(); ack_begin = time.monotonic_ns(); ack = exact(8)
            ack_end = time.monotonic_ns()
            if struct.unpack('<Q',ack)[0] != sequence: raise RuntimeError('Synthetic ACK sequence differs')
            connection.settimeout(remaining()); connection.sendall(struct.pack('<Q',sequence))
            confirm_end = time.monotonic_ns()
            rows.append(dict(sequence=sequence, send_begin_ns=send_begin, send_end_ns=send_end,
                             ack_begin_ns=ack_begin, ack_end_ns=ack_end, confirm_end_ns=confirm_end))
            next_send = send_begin + period  # At most 30Hz; never catch up with a burst.
        connection.shutdown(socket.SHUT_WR); connection.settimeout(remaining())
        if connection.recv(1) != b'': raise RuntimeError('Extra bytes after synthetic confirmation64')
    except Exception as caught:
        error = str(caught)
    finally:
        if connection is not None: connection.close()
    def stats(values):
        return dict(count=len(values), mean_ms=statistics.mean(values), max_ms=max(values)) if values else None
    result = dict(scope='synthetic CPU/network only; no SDK/MMIO/model', passed=error is None and len(rows)==64,
                  error=error, rounds=len(rows), seconds=time.monotonic()-started, TCP_NODELAY=True,
                  send=stats([(r['send_end_ns']-r['send_begin_ns'])/1e6 for r in rows]),
                  ACK_wait=stats([(r['ack_end_ns']-r['ack_begin_ns'])/1e6 for r in rows]), automatic_retry=False)
    with (args.output/'client-timing.jsonl').open('x') as f:
        for row in rows: f.write(json.dumps(row)+'\n')
    with (args.output/'result.json').open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result)); return 0 if result['passed'] else 2


if __name__ == '__main__': raise SystemExit(main())
