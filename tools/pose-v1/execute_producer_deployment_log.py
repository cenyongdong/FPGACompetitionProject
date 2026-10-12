"""One explicit apply/log-only transaction; no forward or retry."""
from pathlib import Path
import getpass,sys,json,hashlib
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';remote='/tmp/pose-producer-deployment-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote,'--log',E/'deployment-directory.log')==0
    archive=E/'deployment-transfer-fixed.tar';assert call('put',archive,remote+'/transfer.tar','--log',E/'deployment-upload.log')==0
    command='set -eu; cd '+remote+'; echo "'+sha(archive)+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_deployment_log; set +e; sh run-producer-deployment.sh > executed-runner.log 2>&1; pose_code=$?; if test ! -f return-apply.tar; then tar -cf return-apply.tar run-apply executed-runner.log; fi; cat executed-runner.log; exit "$pose_code"'
    code=call('ssh',command,'--timeout','360','--log',E/'deployment-launch.log')
    assert call('get',remote+'/return-apply.tar',E/'return-apply.tar','--log',E/'deployment-download.log')==0
    extract_bytes(E/'return-apply.tar',E/'apply-return')
    assert code==0,'Preserve and stop apply-only failure; no re-open'
    print('Official deployment log returned; no forward',flush=True)
finally:secret='';t.getpass.getpass=prompt
