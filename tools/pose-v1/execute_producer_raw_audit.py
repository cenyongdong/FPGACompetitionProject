"""Run one bounded XIR-only RAW extraction; authenticate in memory only."""
from pathlib import Path
import getpass,sys,json,hashlib
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2'
remote='/tmp/pose-producer-reference-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote,'--log',E/'board-directory.log')==0
    assert call('put',E/'transfer.tar',remote+'/transfer.tar','--log',E/'upload.log')==0
    code=call('ssh','set -eu; cd '+remote+'; echo "'+sha(E/'transfer.tar')+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_raw_audit; sh run-producer-raw.sh','--timeout','100','--log',E/'raw-launch.log')
    assert call('get',remote+'/return-raw.tar',E/'return-raw.tar','--log',E/'download.log')==0
    out=E/'raw-return';extract_bytes(E/'return-raw.tar',out);d=out/'run-raw'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    assert code==0 and (d/'exit.txt').read_text().strip()=='0','RAW extraction failed; preserve and stop'
    assert not (d/'stderr.log').read_bytes() and (d/'dmesg.before.log').read_bytes()==(d/'dmesg.after.log').read_bytes()
    rows=[json.loads(x) for x in (d/'parameters.jsonl').read_text().splitlines()]
    assert rows[-1]['status']=='public_RAW_extracted' and rows[-1]['md5_checked'] and not rows[-1]['Device_opened'] and not rows[-1]['Session_created']
    assert len(rows)==23 and len([x for x in rows[:-1] if x['role']=='weight'])==3
    assert not any(x.split()[1].startswith('pose_') for x in (d/'processes.txt').read_text().splitlines()[1:] if len(x.split())>1)
    b=json.loads((E/'transfer/build-result.json').read_text())
    report={'status':'public_XIR_RAW_extraction_passed','program_sha256':b['program_sha256'],'archive_sha256':sha(E/'return-raw.tar'),'rows':rows,'kernel_unchanged':True,'Device_opened':False,'Session_created':False,'NPU_executed':False,'connections_closed':True}
    (E/'raw.review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('RAW extraction returned:',len(rows)-1,'parameters/instructions; no hardware execution')
finally:secret='';t.getpass.getpass=prompt
