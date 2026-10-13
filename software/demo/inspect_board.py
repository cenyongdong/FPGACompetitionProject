"""本轮验证前的只读身份查询；密码仅由遮罩窗口输入并留在内存。"""
from pathlib import Path
import argparse
import getpass
import sys
import ssh_transport as transport


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    secret = transport.credential_dialog()
    original = getpass.getpass
    getpass.getpass = lambda message: secret
    try:
        command = ('set -eu; uname -r; cat /proc/sys/kernel/random/boot_id; '
                   'dpkg-query -W icraft:arm64 customop:arm64; '
                   'sha256sum /usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so '
                   '/usr/lib/aarch64-linux-gnu/libicraft_zg330backend.so; '
                   'cat /sys/class/fpga_manager/fpga0/state; '
                   'ps -eo pid,comm,args; ss -ltnp; '
                   'find /tmp -maxdepth 2 -type d -name "wifi-pose-demo-*"; '
                   'find /tmp -maxdepth 8 -name "scores.f32" -o -name "cases.tsv" | head -20')
        sys.argv = ['transport', 'ssh', command, '--timeout', '30', '--log', str(args.output / 'readonly.txt')]
        try:
            transport.main()
        except SystemExit as error:
            assert (error.code or 0) == 0, 'Board read-only query failed; preserve and stop'
    finally:
        secret = ''
        getpass.getpass = original


if __name__ == '__main__':
    main()
