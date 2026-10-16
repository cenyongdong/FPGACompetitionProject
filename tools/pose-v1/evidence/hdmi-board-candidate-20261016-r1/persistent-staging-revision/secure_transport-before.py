"""专用OpenSSH askpass：只向已核主机的SSH认证子进程提供内存密码，无监听服务。"""
from pathlib import Path
import argparse
import os
import re
import subprocess
import sys

ROOT = Path('D:\\FPGACompetitionProject')
GIT = Path('C:/Program Files/Git/usr/bin')
KNOWN = Path('C:/Users/cenyongdong/.ssh/known_hosts')
KEY = 'AAAAC3NzaC1lZDI1NTE5AAAAIJEJjNFzYnjluPa+kwz4imgxJHRfVt462buoRP0JRtu6'
HOST = 'root@192.168.126.49'
REMOTE = '/tmp/hdmi-board-candidate-20261016-r1/'


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'askpass':
        # 无本地凭证服务器/管道监听；OpenSSH接收此子进程stdout，不计入运行日志。
        prompt = ' '.join(sys.argv[2:])
        if 'root@192.168.126.49' not in prompt or 'password' not in prompt.lower():
            raise RuntimeError('Unrelated authentication request refused')
        match = re.search(r'密码：([^，。\r\n]+)', (ROOT / 'Agents.md').read_text(encoding='utf-8'))
        if not match:
            raise RuntimeError('User-provided credential unavailable')
        secret = match.group(1)
        sys.stdout.write(secret + '\n')
        sys.stdout.flush()
        secret = ''
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['ssh', 'put', 'get'])
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    if not any(line.split()[:3] == ['192.168.126.49', 'ssh-ed25519', KEY] for line in KNOWN.read_text().splitlines()):
        raise RuntimeError('Pinned known-host key differs')
    if args.log.exists() or not 1 <= args.timeout <= 180:
        raise RuntimeError('Fresh log and finite connection budget required')
    helper = Path(__file__).with_name('secure-askpass.sh')
    helper.write_text('#!/bin/sh\nexec "' + Path(sys.executable).as_posix() + '" "' + Path(__file__).as_posix() + '" askpass "$@"\n', encoding='utf-8', newline='\n')
    env = os.environ.copy()
    env.update(SSH_ASKPASS=helper.as_posix(), SSH_ASKPASS_REQUIRE='force', DISPLAY='pose-timing-auth')
    options = ['-F', '/dev/null', '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlgorithms=ssh-ed25519',
               '-o', 'UserKnownHostsFile=' + KNOWN.as_posix(), '-o', 'ConnectTimeout=5',
               '-o', 'NumberOfPasswordPrompts=1', '-o', 'PubkeyAuthentication=no', '-o', 'PreferredAuthentications=password']
    if args.mode == 'ssh':
        command = [str(GIT / 'ssh.exe'), *options, '-T', HOST, args.source]
    else:
        if not args.destination:
            raise RuntimeError('Transfer destination required')
        remote = args.destination if args.mode == 'put' else args.source
        if not remote.startswith(REMOTE) or '..' in remote.split('/'):
            raise RuntimeError('Transfer outside this timing package refused')
        if args.mode == 'get' and Path(args.destination).exists():
            raise RuntimeError('Preserve existing return archive')
        command = [str(GIT / 'scp.exe'), *options, '-q', args.source, HOST + ':' + args.destination] if args.mode == 'put' else [str(GIT / 'scp.exe'), *options, '-q', HOST + ':' + args.source, args.destination]
    result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=args.timeout)
    args.log.write_bytes(result.stdout)
    sys.stdout.buffer.write(result.stdout)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
