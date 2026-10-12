"""Run staged approved group test; release same-Session gate only after review."""
from pathlib import Path
import getpass,sys,json,hashlib,time
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-group-20261011-r2';remote='/tmp/pose-producer-group-20261011-r2'
mode=sys.argv[1];assert mode in ('mock','physical');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
index=0;physical_started=False;physical_finished=False
def call(*args):
    global index
    index+=1;sys.argv=['transport',*map(str,args),'--log',str(E/(mode+'-transport-'+str(index)+'.txt'))]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
def unpack():
    assert call('get',remote+'/return-'+mode+'.tar',E/('return-'+mode+'.tar'))==0
    dest=E/(mode+'-return');extract_bytes(E/('return-'+mode+'.tar'),dest);d=dest/('run-'+mode)
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    return d
def deployment(d,mock):
    assert d['mock']==mock and d['sync_start']==0 and d['layers']==11 and d['member_count']==19 and d['forward_calls']==0
    assert [x['value'] for x in d['boundary']]==[486,478,4386,4390]
    assert [x['bytes'] for x in d['boundary']]==[400,17280,30240,16800]
    for i,x in enumerate(d['boundary']):
        assert not x['is_ocm'] and x['physical']>=x['owned_chunk_start'] and x['bytes']<=x['owned_chunk_capacity']-(x['physical']-x['owned_chunk_start'])
        assert x['alias_from']==([-1,-1,8467,8479][i]) and x['real']==(i<2)
    for i,x in enumerate(d['boundary']):
        for y in d['boundary'][i+1:]:assert x['physical']+x['bytes']<=y['physical'] or y['physical']+y['bytes']<=x['physical']
def fnv(data):
    h=14695981039346656037
    for b in data:h=((h^b)*1099511628211)&((1<<64)-1)
    return h
try:
    if mode=='mock':
        assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote)==0
        assert call('put',E/'transfer.tar',remote+'/transfer.tar')==0
        code=call('ssh','set -eu; cd '+remote+'; echo "'+sha(E/'transfer.tar')+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_group_check pose_producer_payload_selftest; python3 board_producer_run.py mock','--timeout','100')
        d=unpack()
        report={'exit':int((d/'exit.txt').read_text()),'archive_sha256':sha(E/'return-mock.tar'),'kernel_unchanged':(d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes()}
        (E/'mock.exit-review.json').write_text(json.dumps(report,indent=2)+'\n')
        assert code==0 and report['exit']==0 and report['kernel_unchanged'],'Stop and preserve mock failure'
        assert not (d/'stderr.txt').read_bytes();deployment(json.loads((d/'results/deployment.json').read_text()),True)
        assert json.loads((d/'results/release.json').read_text())['remaining_sdk_chunks']==0
        reference=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
        for p in range(2):
            for v,ext in ((486,'f32'),(478,'f16')):
                assert (d/('results/mock-pattern-'+str(p))/('input-'+str(v)+'.roundtrip')).read_bytes()==(reference/('pattern-'+str(p))/('input-'+str(v)+'.'+ext)).read_bytes()
        report.update(status='ARM_payload_mock_deployment_HostCPTR_passed',roundtrip_bytes=35360,nine_rejections=True,NPU_calls=0,release_chunks=0)
        (E/'mock.review.json').write_text(json.dumps(report,indent=2)+'\n');print('ARM payload, mock deployment and 35360-byte HostCPTR passed; no NPU')
    else:
        assert json.loads((E/'mock.review.json').read_text())['status']=='ARM_payload_mock_deployment_HostCPTR_passed'
        # Bind the no-op mock audit to the actually installed board library.
        assert call('ssh','python3 -c "import hashlib; from pathlib import Path; h=hashlib.sha256(Path(\'/usr/lib/aarch64-linux-gnu/libmockzg330.so\').read_bytes()).hexdigest(); print(h); assert h==\'d66064162c72ef8691171a6f92ccedeeb95b3a8eb897347340528a9ee1557776\'"')==0
        # Own finite manager, separate process group, no persistent service.
        launch='cd '+remote+' && python3 -c "import subprocess; from pathlib import Path; assert not Path(\'run-physical\').exists(); p=subprocess.Popen([\'python3\',\'board_producer_run.py\',\'physical\'],stdin=subprocess.DEVNULL,stdout=open(\'physical-manager.stdout.txt\',\'wb\'),stderr=open(\'physical-manager.stderr.txt\',\'wb\'),start_new_session=True); Path(\'physical-manager.pid\').write_text(str(p.pid)+\'\\n\')"'
        assert call('ssh',launch)==0
        physical_started=True
        start=time.monotonic();gate=False
        while time.monotonic()-start<360:
            local=E/('physical-status-'+str(index+1)+'.json')
            # Status only: no additional device data or register reads.
            query='cd '+remote+' && python3 -c "import json; from pathlib import Path; Path(\'status.json\').write_text(json.dumps({\'finished\':Path(\'finished-physical.json\').exists(),\'ready\':Path(\'run-physical/results/deployment.ready\').exists()}))"'
            assert call('ssh',query)==0;assert call('get',remote+'/status.json',local)==0;s=json.loads(local.read_text())
            if s['finished']:physical_finished=True;break
            if s['ready'] and not gate:
                assert call('get',remote+'/run-physical/results/deployment.json',E/'physical-deployment.json')==0
                data=(E/'physical-deployment.json').read_bytes();c=json.loads(data);deployment(c,False)
                assert call('get',remote+'/run-physical/results/deployment.ready',E/'deployment.ready')==0
                assert (E/'deployment.ready').read_text()==str(fnv(data))+'\n'
                memory=E/'pre-forward-memory';memory.mkdir()
                references=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
                for pattern in range(2):
                    for value,extension in ((486,'f32'),(478,'f16')):
                        dest=memory/('pattern-'+str(pattern)+'-'+str(value)+'.roundtrip')
                        assert call('get',remote+'/run-physical/results/memory-pattern-'+str(pattern)+'/input-'+str(value)+'.roundtrip',dest)==0
                        assert dest.read_bytes()==(references/('pattern-'+str(pattern))/('input-'+str(value)+'.'+extension)).read_bytes()
                (E/'deployment.review.json').write_text(json.dumps({'status':'physical_deployment_gate_passed_before_forward','deployment_sha256':hashlib.sha256(data).hexdigest(),'contract':c},indent=2)+'\n')
                assert call('put',E/'deployment.ready',remote+'/run-physical/results/forward.pending')==0
                assert call('ssh','set -eu; test ! -e '+remote+'/run-physical/results/forward.allow; mv '+remote+'/run-physical/results/forward.pending '+remote+'/run-physical/results/forward.allow')==0
                gate=True;print('Physical deployment reviewed; same Session A/B/A/B released',flush=True)
            time.sleep(3)
        else:raise RuntimeError('Finite manager status deadline exceeded; stop and retrieve its preserved evidence')
        d=unpack();code=int((d/'exit.txt').read_text())
        report={'exit':code,'forward_gate_released':gate,'archive_sha256':sha(E/'return-physical.tar'),'kernel_unchanged':(d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes(),'root_cause_resolved':False}
        (E/'physical.exit-review.json').write_text(json.dumps(report,indent=2)+'\n')
        print('Physical stage returned, exit',code,flush=True)
        assert code==0 and report['kernel_unchanged'],'Preserve physical failure; no retry'
finally:
    if physical_started and not physical_finished:
        # Stop our own finite child only; never reopen a failed Session.
        call('ssh','cd '+remote+' && python3 -c "from pathlib import Path; Path(\'abort.request\').write_text(\'controller-error\\n\')"')
        time.sleep(6)
        if not (E/'return-physical.tar').exists():
            call('get',remote+'/return-physical.tar',E/'return-physical.tar')
    secret='';t.getpass.getpass=prompt
