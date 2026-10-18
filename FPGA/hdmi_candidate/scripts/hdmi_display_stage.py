"""Finite, fresh-log SSH stages for the user-resumed HDMI validation package."""
from pathlib import Path
import json
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'tools/pose-v1/evidence/hdmi-display-20261017-r1'
WORK = ROOT / '.local/hdmi-display-20261017-r1'


def main():
    stage, code_name = sys.argv[1:3]
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    assert 1 <= budget <= 180 and stage.replace('-', '').isalnum()
    out = EVIDENCE / stage
    out.mkdir(exist_ok=False)
    code = (EVIDENCE / code_name).read_text(encoding='utf-8')
    (out / 'remote-code.py').write_text(code, encoding='utf-8')
    start = time.monotonic()
    try:
        p = subprocess.run([sys.executable, str(WORK / 'secure_transport.py'), 'ssh',
                            'python3 -c ' + shlex.quote(code), '--timeout', str(budget),
                            '--log', str(out / 'remote.txt')], capture_output=True, timeout=budget + 10)
        (out / 'stdout.txt').write_bytes(p.stdout)
        (out / 'stderr.txt').write_bytes(p.stderr)
        result = {'exit': p.returncode, 'seconds': time.monotonic() - start, 'budget': budget}
        (out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
        if p.returncode:
            print(p.stdout.decode(errors='replace'))
            print(p.stderr.decode(errors='replace'))
            raise SystemExit(p.returncode)
        data = json.loads(p.stdout)
        (out / 'result.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'stage': stage, 'transport_exit': 0, 'seconds': result['seconds'],
                          'result': data.get('summary', {k: data[k] for k in ['boot_id', 'fpga_state', 'device_owners'] if k in data})}, ensure_ascii=False))
    except subprocess.TimeoutExpired as error:
        (out / 'timeout.json').write_text(json.dumps({'seconds': time.monotonic() - start,
                                                       'budget': budget, 'error': str(error)}) + '\n')
        raise


if __name__ == '__main__':
    main()
