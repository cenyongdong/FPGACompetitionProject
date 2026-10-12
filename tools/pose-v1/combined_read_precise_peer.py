"""Prearmed finite 103-window peer; same transport and no data retries."""
import argparse
import hashlib
import json
import socket
import struct
import threading
import time
from pathlib import Path
from combined_read_rtsp_client import LiveClient
from precise_sender_clock import wait_until

class StreamReadyClient(LiveClient):
    def request(self,method,uri=None,headers=None):
        if method!='DESCRIBE' or self.session:
            return super().request(method,uri,headers)
        deadline=time.monotonic()+10;events=[]
        try:
            while True:
                try:
                    result=super().request(method,uri,headers)
                    events.append(dict(status=200,time_pc_ns=time.monotonic_ns()));return result
                except AssertionError as error:
                    if str(error)!='RTSP/1.0 404 Stream Not Found' or time.monotonic()>=deadline:raise
                    events.append(dict(status=404,time_pc_ns=time.monotonic_ns()));time.sleep(.1)
        finally:
            (self.output/'stream-startup.json').write_text(json.dumps(dict(startup_only=True,PLAY_retried=False,input_session_retried=False,events=events))+'\n')



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--fps', type=float, choices=[5.05], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    catalog = []
    for line in (args.package / 'cases.tsv').read_text().splitlines():
        group, name, frame, stamp = line.split()
        if group == 'expanded':
            raw = (args.package / 'inputs' / (name + '.csi')).read_bytes()
            assert len(raw) > 32
            catalog.append((name, raw, int(frame)))
    assert len(catalog) == 27
    scripts = [Path(__file__), Path(__file__).with_name('precise_sender_clock.py'), Path(__file__).with_name('combined_read_rtsp_client.py'),
               Path(__file__).with_name('live_rtsp_client.py'), Path(__file__).with_name('rtsp_replay_client.py')]
    (args.output / 'controller-source.json').write_text(json.dumps(dict(
        sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in scripts},
        startup_only_connection_wait=True, frame_protocol_unchanged=True,
        one_input_session=True, planned_frames=103, fps=args.fps)) + '\n')
    sent, errors = [], []

    def sender():
        report = dict(fps=args.fps, sent=sent, session_count=1,clock='QueryPerformanceCounter',last_tail_poll_ns=2000000,no_system_timer_change=True)
        try:
            deadline = time.monotonic() + 110
            while True:
                try:
                    connection = socket.create_connection(('192.168.126.49', 39001), 1)
                    break
                except (ConnectionRefusedError, TimeoutError):
                    assert time.monotonic() < deadline, 'First input listener timed out'
                    time.sleep(.1)
            with connection:
                connection.settimeout(5)
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                epoch_ns = time.perf_counter_ns()
                for i in range(103):
                    scheduled_ns=epoch_ns+round(i*1e9/args.fps)
                    wait_until(scheduled_ns)
                    name, original, fixture = catalog[i % 27]
                    raw = bytearray(original)
                    struct.pack_into('<Q', raw, 16, 100000 + i)
                    assert raw[:16] == original[:16] and raw[24:] == original[24:]
                    before = time.perf_counter_ns()
                    connection.sendall(raw)
                    sent.append(dict(sequence=i, transport_id=100000+i, case=name,
                        fixture_frame_id=fixture, sha256=hashlib.sha256(raw).hexdigest(),
                        payload_sha256=hashlib.sha256(raw[32:]).hexdigest(),
                        scheduled_pc_ns=scheduled_ns,begin_pc_ns=before,end_pc_ns=time.perf_counter_ns()))
            report['status'] = 'sent_no_receiver_ack'
        except Exception as error:
            errors.append(error)
            report.update(status='failed', error=str(error))
        finally:
            (args.output / 'sender.json').write_text(json.dumps(report, indent=2)+'\n')

    worker = threading.Thread(target=sender)
    worker.start()
    client = None
    print('PEER_ARMED: 103 windows; first listeners only, no data retries', flush=True)
    try:
        deadline = time.monotonic()+110
        while True:
            try:
                client = StreamReadyClient(args.output)
                break
            except (ConnectionRefusedError, TimeoutError):
                assert time.monotonic() < deadline, 'First RTSP listener timed out'
                time.sleep(.1)
        result = client.run_live()
        client.save(result)
    except Exception as error:
        if client:
            client.save(dict(status='failed', error=str(error), frames=client.frames,
                             packets=client.packet_log))
        raise
    finally:
        if client:
            client.sock.close()
        worker.join(timeout=115)
    assert not worker.is_alive() and not errors and len(sent) == 103, str(errors)
    print('Finite coverage peer completed:', len(client.frames), 'AUs', flush=True)


if __name__ == '__main__':
    main()
