"""Use existing pinned SSH and one-use memory authentication; never save secrets."""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from device_credentials import credentials


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('mode', choices=('ssh','put','get'))
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--reverse', action='store_true')
    parser.add_argument('--stream', action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.label):raise ValueError('Invalid log label')
    out=ROOT/'.local/pose180-pipeline-20261025-r1'
    out.mkdir(exist_ok=True)
    module_path=ROOT/'demo_v1/tools/ssh.py'
    spec=importlib.util.spec_from_file_location('_pose180_pinned_ssh',module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Read private local configuration or hidden input; SSH uses one-use IPC.
    def authorized_password(_prompt):
        user, password = credentials('192.168.126.49', 'root')
        if user != 'root':raise ValueError('This board transport requires the root account')
        return password
    module.getpass.getpass=authorized_password
    sys.argv=[str(module_path),args.mode,args.source]
    if args.destination:sys.argv.append(args.destination)
    sys.argv+=['--timeout',str(args.timeout),'--log',str(out/(args.label+'.log'))]
    if args.reverse:sys.argv.append('--reverse')
    if args.stream:sys.argv.append('--stream')
    module.main()


if __name__=='__main__':main()
