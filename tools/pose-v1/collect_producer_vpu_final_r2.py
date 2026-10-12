"""Collect corrected audit in new directory; no inference or encoder restart."""
from pathlib import Path
import getpass, hashlib, json, sys
import ssh_memory_transport as t
from archive_bytes import extract_bytes

R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/producer-vpu-20261011-r2'
remote = '/tmp/pose-producer-vpu-20261011-r2'
source = R / 'tools/pose-v1/board_producer_vpu_final_r2.py'
secret = getpass.getpass('Authorized Lite password (memory only): ')
prompt = t.getpass.getpass
t.getpass.getpass = lambda _: secret

def call(*args):
    sys.argv = ['transport', *map(str, args)]
    try:
        t.main()
    except SystemExit as e:
        return e.code or 0
    return 0

try:
    assert call('put', source, remote + '/board_producer_vpu_final_r2.py', '--log', E / 'final-r2-upload.txt') == 0
    h = hashlib.sha256(source.read_bytes()).hexdigest()
    cmd = 'set -eu; cd ' + remote + '; echo "' + h + '  board_producer_vpu_final_r2.py" | sha256sum -c -; LC_ALL=C.UTF-8 python3 board_producer_vpu_final_r2.py'
    assert call('ssh', cmd, '--log', E / 'final-r2-operation.txt') == 0
    assert call('get', remote + '/return-final-r2.tar', E / 'return-final-r2.tar', '--log', E / 'final-r2-download.txt') == 0
    extract_bytes(E / 'return-final-r2.tar', E / 'final-r2-return')
    for directory in ('final', 'final-r2'):
        d = E / 'final-r2-return' / directory
        for line in (d / 'files.sha256').read_text().splitlines():
            digest, name = line.split('  ', 1)
            assert hashlib.sha256((d / name).read_bytes()).hexdigest() == digest
    assert json.loads((E / 'final-r2-return/final-r2/review.json').read_text())['status'] == 'read_only_final_identity_cleanup_passed'
    print('Final archive hashes and cleanup verified; all transport processes exited')
finally:
    secret = ''
    t.getpass.getpass = prompt
