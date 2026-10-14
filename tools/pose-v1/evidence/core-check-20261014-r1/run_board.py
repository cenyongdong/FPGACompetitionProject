"""本次CPU107与三窗口检查包装；只适配新目录和内存认证，原检查器不改。"""
from pathlib import Path
import getpass
import hashlib
import json
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
DEMO = ROOT / 'software/demo'
OLD_REMOTE = '/tmp/wifi-pose-demo-refactor-20261013-r1'
REMOTE = '/tmp/wifi-pose-demo-core-check-20261014-r1'
BUILD = ROOT / '.local/pose-v1-build/demo-core-check-20261014-r1'


def adapted(name):
    path = DEMO / (name + '.py')
    original = path.read_text(encoding='utf-8')
    current = original.replace(OLD_REMOTE, REMOTE)
    copy = EVIDENCE / ('harness-' + name + '.py')
    assert not copy.exists()
    copy.write_text(current, encoding='utf-8', newline='\n')
    value = types.ModuleType(name)
    value.__file__ = str(path)
    sys.modules[name] = value
    exec(compile(current, str(path), 'exec'), value.__dict__)
    return value


def main():
    sys.path.insert(0, str(DEMO))
    build = json.loads((BUILD / 'build-result.json').read_text())
    assert build['status'] == 'compiled_not_board_executed'
    # 使用用户已写入执行授权的凭据，读取后仅保留在进程内存；不复制或输出。
    match = re.search(r'密码：([^，\r\n]+)', (ROOT / 'Agents.md').read_text(encoding='utf-8'))
    if match is None:
        raise RuntimeError('Authorized memory credential unavailable')
    secret = match.group(1)
    match = None
    transport = adapted('ssh_transport')
    adapted('deploy')
    validator = adapted('validate_board')
    original = getpass.getpass
    getpass.getpass = lambda message: secret
    transport.credential_dialog = lambda: secret
    try:
        # 首次连接只读核验内核、库、FPGA状态及占用；不启动负载。
        command = ('set -eu; uname -r; cat /proc/sys/kernel/random/boot_id; '
                   'sha256sum /usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so '
                   '/usr/lib/aarch64-linux-gnu/libicraft_zg330backend.so; '
                   'cat /sys/class/fpga_manager/fpga0/state; ps -eo pid,comm,args; ss -ltnp')
        sys.argv = ['transport', 'ssh', command, '--timeout', '30',
                    '--log', str(EVIDENCE / 'board-readonly.txt')]
        try:
            transport.main()
        except SystemExit as error:
            assert (error.code or 0) == 0, 'Read-only audit failed; stop'
        readonly = (EVIDENCE / 'board-readonly.txt').read_text()
        assert readonly.splitlines()[0] == '5.4.52'
        for name in ('libicraft_hostbackend.so', 'libicraft_zg330backend.so'):
            assert build['libraries'][name] + '  /usr/lib/aarch64-linux-gnu/' + name in readonly
        assert 'operating' in readonly.splitlines()
        assert not any(len(line.split()) > 1 and line.split()[1].startswith('pose_')
                       for line in readonly.splitlines())
        assert ':39001 ' not in readonly and ':8554 ' not in readonly
        sys.argv = ['validate_board', '--build', str(BUILD), '--evidence', str(EVIDENCE / 'board')]
        validator.main()
        board = EVIDENCE / 'board'
        old = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1/board/host-return/run-host'
        actual = (board / 'host-return/run-host/before.dmesg.txt').read_text()
        expected = (old / 'before.dmesg.txt').read_text()
        assert re.search(r'Linux version [^\r\n]+', actual).group() == re.search(r'Linux version [^\r\n]+', expected).group()
        (EVIDENCE / 'board-wrapper-review.json').write_text(json.dumps({
            'status': 'passed', 'remote': REMOTE,
            'adaptation': 'Only new remote path and credential source; original scripts unchanged',
            'CPU_budget_seconds': 300, 'short_budget_seconds': 180,
            'kernel_same_as_prior_evidence': True, 'no_60_window_run': True,
            'old_DATA_investigation': 'paused',
            'original_scripts': {name: hashlib.sha256((DEMO / (name + '.py')).read_bytes()).hexdigest()
                                 for name in ('ssh_transport', 'deploy', 'validate_board')}
        }, indent=2) + '\n', encoding='utf-8')
    finally:
        secret = ''
        getpass.getpass = original


if __name__ == '__main__':
    main()
