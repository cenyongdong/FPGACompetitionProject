"""Temporary private-link distributor, bounded job queue and UDP delivery ledger."""
import argparse
import csv
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import socket
import struct
import threading
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', choices=['192.168.137.1', '192.168.50.102', '127.0.0.1'], required=True)
    parser.add_argument('--peer', default='192.168.137.61')
    parser.add_argument('--management-peer', help='Optional second explicit IPv4 peer for HTTP control only')
    parser.add_argument('--phone-gateway', action='store_true', help='Send to owned iPhone gateway 172.20.10.1; no UDP delivery ledger is available there')
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--control-only', action='store_true', help='Use an existing laptop sender; do not distribute executable files')
    parser.add_argument('--access-executable', type=Path)
    parser.add_argument('--seconds', type=int, default=1200)
    args = parser.parse_args()
    if args.control_only and (args.executable or args.access_executable):
        parser.error('Control-only mode does not distribute executables')
    if not args.control_only and args.executable is None:
        parser.error('--executable is required unless --control-only is selected')
    ipaddress.IPv4Address(args.peer)
    if args.management_peer:
        address = ipaddress.IPv4Address(args.management_peer)
        if not address.is_private:
            raise ValueError('Management peer must be a private IPv4 address')
    destination = '172.20.10.1' if args.phone_gateway else args.bind
    if not 10 <= args.seconds <= 1800:
        raise ValueError('Invalid control lifetime')
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / 'jobs').mkdir()
    executable = args.executable.read_bytes() if args.executable else None
    access_executable = args.access_executable.read_bytes() if args.access_executable else None
    lock = threading.Lock()
    stop = threading.Event()
    receivers = {}
    peer = '127.0.0.1' if args.bind == '127.0.0.1' else args.peer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, body, mime='application/json'):
            body = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            return self.client_address[0] in (peer, args.management_peer, '127.0.0.1')

        def do_GET(self):
            if not self.allowed():
                return self.reply(403, {'error': 'Unexpected peer'})
            if self.path == '/':
                if args.control_only:
                    return self.reply(200, {'mode':'control_only','executable_distribution':False})
                return self.reply(200, '<meta charset="utf-8"><h2>MT7922 临时发射验证</h2><p>无需安装，关闭窗口结束。只执行50/300Hz有界UDP测试。</p><p><a href="/LaptopTx.exe">下载 LaptopTx.exe</a></p>'.encode(), 'text/html; charset=utf-8')
            if self.path == '/LaptopTx.exe' and executable is not None:
                return self.reply(200, executable, 'application/octet-stream')
            if self.path == '/LaptopSshAccess.exe' and access_executable is not None:
                return self.reply(200, access_executable, 'application/octet-stream')
            if self.path != '/task':
                return self.reply(404, {})
            with lock:
                pending = sorted((root / 'jobs').glob('*.pending.json'))
                if not pending:
                    return self.reply(200, None)
                job = json.loads(pending[0].read_text(encoding='utf-8-sig'))
                valid = (uuid.UUID(hex=job['id']).hex == job['id'] and job['hz'] in (50, 300)
                         and job['seconds'] in (2, 10, 20) and job['destination'] == destination)
                if not valid:
                    return self.reply(400, {'error': 'Invalid bounded job'})
                pending[0].rename(pending[0].with_name(job['id'] + '.assigned.json'))
                receivers.setdefault(job['id'], {'rows': [], 'source': None})
            self.reply(200, job)

        def do_POST(self):
            if not self.allowed():
                return self.reply(403, {'error': 'Unexpected peer'})
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2000000:
                return self.reply(413, {})
            raw = self.rfile.read(length)
            data = json.loads(raw)
            if self.path == '/access-info':
                if access_executable is None or data.get('computer_name') != 'DESKTOP-V4Q9HC6' or data.get('mac') != '50:bb:b5:db:a5:02':
                    return self.reply(400, {})
                with lock:
                    with (root / 'access-info.json').open('x', encoding='utf-8') as stream:
                        json.dump(data, stream, indent=2, ensure_ascii=False)
                return self.reply(200, {'ok': True})
            if self.path == '/inventory':
                target = root / 'inventory.json'
                with lock:
                    if not target.exists():
                        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                return self.reply(200, {'ok': True})
            if self.path != '/result':
                return self.reply(404, {})
            job_id = data['id']
            if uuid.UUID(hex=job_id).hex != job_id or not (root / 'jobs' / (job_id + '.assigned.json')).is_file():
                return self.reply(400, {})
            target = root / (job_id + '-sender.json')
            with lock:
                if target.exists():
                    return self.reply(200 if target.read_bytes() == raw else 409, {'already_returned': True})
                target.write_bytes(raw)
                rows = list(receivers.get(job_id, {}).get('rows', []))
                with (root / (job_id + '-delivery.csv')).open('x', newline='', encoding='utf-8') as stream:
                    writer = csv.writer(stream)
                    writer.writerow(('receive_mono_ns', 'slot', 'sender_before_ns', 'sender_target_ns', 'source', 'bytes'))
                    writer.writerows(rows)
                slots = [r[1] for r in rows]
                summary = dict(job_id=job_id, datagrams=len(rows), unique_slots=len(set(slots)),
                               duplicate_slots=len(slots)-len(set(slots)),
                               source=receivers.get(job_id, {}).get('source'), hardware_test=args.bind != '127.0.0.1',
                               limitation='IP delivery ledger; not RF timestamps or CSI evidence')
                if args.phone_gateway:
                    summary.update(applicable=False, limitation='No UDP receiver runs on the owned phone gateway; zero ledger entries do not measure packet loss')
                (root / (job_id + '-delivery.json')).write_text(json.dumps(summary, indent=2), encoding='utf-8')
            self.reply(200, {'ok': True})

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    udp.bind((args.bind, 39031))
    udp.settimeout(.25)

    def receive():
        with (root / 'udp-arrivals.csv').open('x', newline='', buffering=1, encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(('job_id', 'receive_mono_ns', 'slot', 'sender_before_ns', 'sender_target_ns', 'source', 'bytes'))
            while not stop.is_set():
                try:
                    data, endpoint = udp.recvfrom(2048)
                except socket.timeout:
                    continue
                stamp = time.perf_counter_ns()
                if endpoint[0] != peer or len(data) != 256 or data[:8] != b'CSI300V1':
                    continue
                job_id = data[32:48].hex()
                slot, before, target = struct.unpack_from('<QQQ', data, 8)
                row = (stamp, slot, before, target, endpoint[0], len(data))
                with lock:
                    current = receivers.get(job_id)
                    if current is None or len(current['rows']) >= 20000:
                        continue
                    current['source'] = endpoint[0]
                    current['rows'].append(row)
                writer.writerow((job_id,) + row)

    server = ThreadingHTTPServer((args.bind, 39032), Handler)
    server.timeout = .25
    record = dict(pid=__import__('os').getpid(), bind=args.bind, destination=destination, peer=peer, lifetime_s=args.seconds,
                  executable_sha256=hashlib.sha256(executable).hexdigest() if executable is not None else None,
                  executable_distribution=not args.control_only,started_unix=time.time())
    (root / 'control.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    worker = threading.Thread(target=receive, daemon=True)
    worker.start()
    deadline = time.monotonic() + args.seconds
    print(json.dumps(record), flush=True)
    try:
        while time.monotonic() < deadline and not (root / 'STOP').exists():
            server.handle_request()
    finally:
        stop.set()
        worker.join(timeout=2)
        udp.close()
        server.server_close()
        (root / 'closed.json').write_text(json.dumps(dict(closed_unix=time.time())), encoding='utf-8')


if __name__ == '__main__':
    main()
