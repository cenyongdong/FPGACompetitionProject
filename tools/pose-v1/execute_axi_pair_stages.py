"""Run each approved fresh stage once; return/review before the next stage.

Password is obtained once in-process and used only by the existing memory IPC
transport. It is never put in argv, environment, files or captured logs.
"""
from pathlib import Path
import getpass,sys,subprocess,json,hashlib
from archive_bytes import extract_bytes
import ssh_memory_transport as transport
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'tools/pose-v1/evidence/axi-pair-20261011-r4';remote='/tmp/pose-axi-pair-20261011-r4'
stages={'memory':['copy','read'],'vpu':['copy-vpu','read-vpu']}[sys.argv[1]]
secret=getpass.getpass('Authorized Lite password (memory only): ')
original_prompt=getpass.getpass
transport.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['ssh_memory_transport.py',*map(str,args)]
    try:transport.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    if stages[0]=='copy-vpu':
        assert call('put',ROOT/'tools/pose-v1/compact_typed_before_vpu.py',remote+'/resource-policy.py','--log',E/'upload-resource-policy.log')==0
    for stage in stages:
        if stage.endswith('vpu'):
            command='set -eu; cd '+remote+'; python3 resource-policy.py resource-'+stage+'; cp resource-policy.py resource-'+stage+'/executed-policy.py; tar -cf return-resource-'+stage+'.tar resource-'+stage+'; sha256sum return-resource-'+stage+'.tar'
            assert call('ssh',command,'--timeout','120','--log',E/(stage+'-resource.log'))==0
            archive=E/('return-resource-'+stage+'.tar')
            assert call('get',remote+'/'+archive.name,archive,'--log',E/('download-resource-'+stage+'.log'))==0
            out=E/('resource-'+stage);extract_bytes(archive,out)
            d=out/('resource-'+stage);report=json.loads((d/'decision.json').read_text());assert report['kernel_unchanged'] and report['compaction_writes'] in (0,1)
            assert hashlib.sha256((d/'executed-policy.py').read_bytes()).digest()==hashlib.sha256((ROOT/'tools/pose-v1/compact_typed_before_vpu.py').read_bytes()).digest()
            print('Recorded resource preparation',stage,report['compaction_writes'],report['ordinary_512KiB_units_before'],flush=True)
        print('Starting fresh stage',stage,flush=True)
        code=call('ssh','set -eu; cd '+remote+'; sh run-axi-pair.sh '+stage,'--timeout','240','--log',E/(stage+'-launch.log'))
        returned=call('get',remote+'/return-'+stage+'.tar',E/('return-'+stage+'.tar'),'--log',E/('download-'+stage+'.log'))
        assert returned==0 and code==0,(stage,code,returned)
        p=subprocess.run([sys.executable,str(ROOT/'tools/pose-v1/review_axi_pair_probe.py'),stage]);assert p.returncode==0
        assert call('put',E/('review-'+stage+'.json'),remote+'/review-'+stage+'.json','--log',E/('upload-'+stage+'-review.log'))==0
        print('Stage returned and independently reviewed:',stage,flush=True)
finally:
    secret='';transport.getpass.getpass=original_prompt
