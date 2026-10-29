"""Linux container tests: real guard/capture, simulated endpoint and boot hooks."""
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

SOURCE = Path(__file__).resolve().parent


def wait_for(predicate, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError('condition timed out')


def run(out):
    guard = str(out / 'build/router_guard-native')
    capture = str(out / 'build/capture-native')
    results = {}
    folder = out / 'tests/rx'
    folder.mkdir(parents=True)
    (folder / 'armed').touch()
    for budget in ('0', 'invalid'):
        assert subprocess.run([guard, 'rx', str(folder), budget, '127.0.0.1', '39033', 'lo']).returncode == 2
    (folder / 'continuous').touch()
    (folder / 'restore.sh').write_text('touch restored; rm -f armed\n')
    fake = folder / 'capture-metadata-stream'
    fake.write_text('#!' + sys.executable + '\nimport os,sys,time\n'
                    'assert sys.argv[2:]==["-","0","0"]\n'
                    'while True:\n os.write(1,b"fresh"*100);time.sleep(.01)\n')
    fake.chmod(0o755)
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    port = server.getsockname()[1]
    # Bind without listening first: RX must survive an unavailable consumer.
    subprocess.run([guard, 'rx', str(folder), '0', '127.0.0.1', str(port), 'lo'], check=True)
    try:
        time.sleep(2.5)
        assert not (folder / 'guard-final.json').exists()
        server.listen(1)
        server.settimeout(12)
        peer, _ = server.accept()
        with peer:
            peer.settimeout(3)
            assert peer.recv(500).startswith(b'fresh')
        peer, _ = server.accept()
        with peer:
            peer.settimeout(3)
            assert peer.recv(500).startswith(b'fresh')
    finally:
        (folder / 'stop.request').touch()
        server.close()
        wait_for(lambda: (folder / 'guard-final.json').exists())
    final = json.loads((folder / 'guard-final.json').read_text())
    assert final['guard_fault'] == final['restore_exit'] == 0 and final['generations'] == 2, final
    assert len(list(folder.glob('capture-*.json'))) <= 4
    results['late_endpoint_and_reconnect'] = final

    # Continuous raw capture cannot be selected for a file, or by bad arguments.
    for dest, seconds, packets in ((str(folder / 'bad.pcap'), '0', '0'), ('-', 'bad', '0'), ('-', '0', '4000000')):
        assert subprocess.run([capture, 'lo', dest, seconds, packets], capture_output=True).returncode == 2
    process = subprocess.Popen([capture, 'lo', '-', '0', '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        time.sleep(.15)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            for _ in range(5):
                udp.sendto(b'CSI test', ('127.0.0.1', 5500))
                time.sleep(.05)
        assert process.poll() is None
    finally:
        process.terminate()
        raw, log = process.communicate(timeout=3)
    receipt = json.loads(log)
    assert receipt['packets'] >= 5 and receipt['packet_budget_reached'] == 0 and receipt['interrupted'] == 1, receipt
    assert len(raw) > 24
    results['pipe_capture_stop'] = receipt

    # This test runs only in a disposable container, without eth6/radio access.
    assert not Path('/sys/class/net/eth6').exists()
    install = Path('/jffs/pose180-csi')
    (install / 'runtime').mkdir(parents=True)
    shutil.copyfile(SOURCE / 'service.sh', install / 'service.sh')
    (install / 'enabled').touch()
    (install / 'runtime/identity.conf').write_text('ROUTER_IP=192.168.50.1\nROUTER_MAC=00:00:00:00:00:00\nGUARD_ROLE=rx\n')
    service = ['sh', str(install / 'service.sh')]
    subprocess.run(service + ['boot'], check=True)
    pid = Path('/tmp/pose180-csi/service.pid').read_text()
    subprocess.run(service + ['boot'], check=True)
    assert Path('/tmp/pose180-csi/service.pid').read_text() == pid
    subprocess.run(service + ['stop'], check=True)
    subprocess.run(service + ['start'], check=True)
    assert Path('/tmp/pose180-csi.previous/restored').exists()
    subprocess.run(service + ['disable'], check=True)
    assert not (install / 'enabled').exists()
    results['boot_duplicate_stop_restart_disable'] = 'passed'
    (out / 'tests/result.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results))


if __name__ == '__main__':
    run(Path(sys.argv[1]).resolve())
