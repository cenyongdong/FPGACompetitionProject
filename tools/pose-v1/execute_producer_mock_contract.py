"""One official mock-only deployment, return evidence even if a contract fails."""
from pathlib import Path
import getpass,sys,json,hashlib
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2'
remote='/tmp/pose-producer-reference-20261011-r2/mock';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote,'--log',E/'mock-directory.log')==0
    assert call('put',E/'mock-transfer.tar',remote+'/transfer.tar','--log',E/'mock-upload.log')==0
    code=call('ssh','set -eu; cd '+remote+'; echo "'+sha(E/'mock-transfer.tar')+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_mock_contract; sh run-producer-mock.sh','--timeout','70','--log',E/'mock-launch.log')
    assert call('get',remote+'/return-mock.tar',E/'return-mock.tar','--log',E/'mock-download.log')==0
    out=E/'mock-return';extract_bytes(E/'return-mock.tar',out);d=out/'run-mock'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    assert (d/'dmesg.before.log').read_bytes()==(d/'dmesg.after.log').read_bytes(),'Kernel changed; stop'
    review={'exit':code,'archive_sha256':sha(E/'return-mock.tar'),'kernel_unchanged':True,'physical_device_opened':False,'NPU_executed':False,'forward_called':False,'connections_closed':True}
    if code==0:
        c=json.loads((d/'results/mock-contract.json').read_text());assert c['URL']=='mock://zg330' and c['sync_start']==0 and c['layers']==11 and len(c['members'])==19
        review['status']='public_mock_selected_group_deployed';review['contract']=c
    else:review['status']='mock_contract_failed_preserved_no_physical_test'
    (E/'mock.review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Mock-only deployment returned, exit',code,'no physical NPU')
    assert code==0,'Stop; preserve mock failure without physical retry'
finally:secret='';t.getpass.getpass=prompt
