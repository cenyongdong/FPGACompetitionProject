"""Linux loopback only. Proves recorder bounds/framing, never radio capture."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

from csi_verify import verify
from test_csi_verify import MAC, payload


def main(binary, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    pcap = output / 'loopback-fixture.pcap'
    sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sink.bind(('127.0.0.1', 5500))
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    process = subprocess.Popen([binary, 'lo', str(pcap), '2', '60'], stderr=subprocess.PIPE)
    try:
        time.sleep(0.2)
        for seq in range(20):
            for core in [0, 1, 2]:
                sender.sendto(payload(core, seq, chip=106), ('127.0.0.1', 5500))
                time.sleep(0.001)
        _, log = process.communicate(timeout=4)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        sender.close()
        sink.close()
    assert process.returncode == 0, log
    acquisition = verify(pcap, 64, [0, 1, 2], 0, 106, MAC)
    assert acquisition['acquisition_pass'], acquisition
    overwrite = subprocess.run([binary, 'lo', str(pcap), '1', '1'], capture_output=True)
    assert overwrite.returncode == 3
    started = time.monotonic()
    empty = subprocess.run([binary, 'lo', str(output / 'empty.pcap'), '1', '1'],
                           capture_output=True, timeout=3)
    elapsed = time.monotonic() - started
    assert empty.returncode == 5 and elapsed < 2.5
    invalid = subprocess.run([binary, 'lo', str(output / 'invalid.pcap'), '61', '1'], capture_output=True)
    assert invalid.returncode == 2
    result = dict(passed=True, radio_test=False, recorder=json.loads(log),
                  offline_verifier=acquisition, overwrite_rejected=True,
                  no_input_stops=True, no_input_wall_s=elapsed, excessive_budget_rejected=True)
    (output / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    main(*sys.argv[1:])
