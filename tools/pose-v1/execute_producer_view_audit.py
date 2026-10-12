"""Execute the approved XIR-only offline inspector once and return its evidence."""
from pathlib import Path
import getpass,sys,json,hashlib
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';remote='/tmp/pose-producer-contract-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote,'--log',E/'board-directory.log')==0
    assert call('put',E/'transfer.tar',remote+'/transfer.tar','--log',E/'upload.log')==0
    code=call('ssh','set -eu; cd '+remote+'; echo "'+sha(E/'transfer.tar')+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_view_audit; sh run-producer-view.sh','--timeout','60','--log',E/'offline-launch.log')
    assert call('get',remote+'/return-offline.tar',E/'return-offline.tar','--log',E/'download.log')==0
    assert code==0,'Stop and preserve failed offline inspector'
    out=E/'offline-return';extract_bytes(E/'return-offline.tar',out);d=out/'run-offline'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    assert (d/'exit.txt').read_text().strip()=='0' and not (d/'stderr.log').read_bytes()
    assert (d/'dmesg.before.log').read_bytes()==(d/'dmesg.after.log').read_bytes()
    data=json.loads((d/'views.json').read_text());assert data['status']=='offline_public_views_inspected' and not data['Device_opened'] and not data['Session_created'] and not data['RAW_loaded']
    assert len(data['views'])==3 and len(data['views'][2]['members'])==19 and [x['op'] for x in data['producer_ops']]==[8629,8631]
    assert not any(line.split()[1].startswith('pose_') for line in (d/'processes.txt').read_text().splitlines()[1:] if len(line.split())>1)
    report={'status':'public_XIR_offline_views_passed_no_hardware_execution','archive_sha256':sha(E/'return-offline.tar'),'views_sha256':sha(d/'views.json'),'groups':data['views'],'program_sha256':json.loads((E/'transfer/build-result.json').read_text())['program_sha256'],'Device_opened':False,'Session_created':False,'kernel_unchanged':True,'all_programs_connections_closed':True}
    (E/'offline.review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Offline public views inspected and returned',[(x['name'],len(x['inputs']),len(x['outputs'])) for x in data['views']])
finally:secret='';t.getpass.getpass=prompt
