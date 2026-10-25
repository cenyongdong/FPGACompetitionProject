"""Pinned, read-only remote identity check for the resumed PS diagnostic."""
from pathlib import Path
import json
import shlex
import subprocess
import sys
import argparse

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path,default=E)
    parser.add_argument('--attempt',type=int,default=1)
    parser.add_argument('--repository-root',type=Path,default=R)
    args=parser.parse_args();evidence=args.evidence.resolve();evidence.mkdir(parents=True,exist_ok=True)
    assets=args.repository_root.resolve()
    if args.attempt<1:raise ValueError('Attempt must be positive')
    stem='resume-preflight'+('' if args.attempt==1 else '-r'+str(args.attempt))
    functions = (R / 'tools/pose-v1/board_application_preflight.py').read_text().split('out=pathlib.Path(sys.argv[1])')[0]
    expected = json.loads((assets / 'tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/final-audit.json').read_text())
    expected = {k: expected[k] for k in ('startup_files', 'SDK')}
    code = functions + '\nexpected=' + repr(expected) + '\n' + '''
import os
files={x['name']:{'size':x['size'],'sha256':x['sha256']} for x in fat_files()}
libs={n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['SDK']}
owners=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try: fds=list((p/'fd').iterdir())
 except OSError:continue
 for fd in fds:
  try:t=os.readlink(fd)
  except OSError:continue
  if t.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri')):
   owners.append({'pid':p.name,'target':t})
result={'scope':'read-only FAT, SDK files and proc; no SDK loading or MMIO',
 'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'startup_files':files,'SDK':libs,'device_owners':owners,
 'startup_match':all(files.get(n)==v for n,v in expected['startup_files'].items()),
 'SDK_match':libs==expected['SDK'],
 'memory':pathlib.Path('/proc/meminfo').read_text(),
 'cmdline':pathlib.Path('/proc/cmdline').read_text().strip()}
print(json.dumps(result,indent=2))
'''
    (evidence / (stem+'-code.py')).write_text(code)
    log = evidence / (stem+'.log')
    if log.exists():raise FileExistsError('Preserve existing preflight; select a new attempt')
    transport = assets / '.local/hdmi-live-20261017-r3/secure_transport.py'
    p = subprocess.run([sys.executable, str(transport), 'ssh', 'python3 -c ' + shlex.quote(code),
                        '--timeout', '30', '--log', str(log)], capture_output=True)
    (evidence / (stem+'-stderr.log')).write_bytes(p.stderr)
    if p.returncode:
        print(json.dumps({'exit_code': p.returncode, 'log': str(log)}))
        raise SystemExit(p.returncode)
    result = json.loads(log.read_text())
    (evidence / 'resume-preflight.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ('boot_id', 'startup_match', 'SDK_match', 'device_owners')}))
    if not result['startup_match'] or not result['SDK_match'] or result['device_owners']:
        raise SystemExit('Identity/occupancy mismatch; preserve before board mutation')


if __name__ == '__main__':
    main()
