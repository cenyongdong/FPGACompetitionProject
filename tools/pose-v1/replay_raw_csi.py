"""Send original CSI windows over TCP; no preprocessing, prediction, or GT."""
import argparse
import socket
import time
from pathlib import Path
from csi_io import encode_window, load_mat


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', required=True)
    p.add_argument('--port', type=int, default=39001)
    p.add_argument('--csi-dir', required=True, type=Path)
    p.add_argument('--prefix', required=True)
    p.add_argument('--start', required=True, type=int)
    p.add_argument('--end', required=True, type=int)
    p.add_argument('--fps', type=float, default=10)
    args = p.parse_args()
    if args.end < args.start or not 0 < args.fps <= 30:
        p.error('Invalid range or fps (0,30]')
    files = [args.csi_dir / f'{args.prefix}_{n}.mat' for n in range(args.start, args.end+1)]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    # Each record is 32-byte header + 86400-byte raw float64 I/Q payload.
    with socket.create_connection((args.host,args.port), timeout=5) as stream:
        stream.settimeout(5)
        stream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        origin = time.monotonic()
        for index, path in enumerate(files):
            wait = origin + index / args.fps - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            stream.sendall(encode_window(load_mat(path), index, time.time_ns()))
            print(f'sent frame={index} file={path.name}')


if __name__ == '__main__':
    main()
