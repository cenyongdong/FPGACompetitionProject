"""Only collect final audit; no inference/encoder/reboot."""
from pathlib import Path
import getpass,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'tools/pose-v1/evidence/demo-20261011-r4';remote='/tmp/wifi-pose-demo-20261011-r4'
sys.path.insert(0,str(ROOT/'tools/pose-v1'))
import ssh_memory_transport as t
from archive_bytes import extract_bytes
assert json.loads((E/'demo.video-review.json').read_text())['status']=='original_VPU_video_real_pose_geometry_verified'
source=Path(__file__).parent/'board/final_audit.py';secret=getpass.getpass('Authorized Lite password (memory only): ');original=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('put',source,remote+'/final_audit.py','--log',E/'final-upload.txt')==0
    h=hashlib.sha256(source.read_bytes()).hexdigest()
    assert call('ssh','set -eu; cd '+remote+'; echo "'+h+'  final_audit.py" | sha256sum -c -; python3 final_audit.py','--log',E/'final-operation.txt')==0
    assert call('get',remote+'/return-final.tar',E/'return-final.tar','--log',E/'final-download.txt')==0
    extract_bytes(E/'return-final.tar',E/'final-return');d=E/'final-return/final'
    for line in (d/'files.sha256').read_text().splitlines():digest,name=line.split('  ',1);assert hashlib.sha256((d/name).read_bytes()).hexdigest()==digest
    print('Final audit returned; connections closed')
finally:secret='';t.getpass.getpass=original
