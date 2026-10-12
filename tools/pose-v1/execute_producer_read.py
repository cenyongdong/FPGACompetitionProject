"""Host -> off -> on finite execution, same ELF; passwords remain in memory."""
from pathlib import Path
import json,hashlib,getpass,sys,time
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r1';remote='/tmp/pose-producer-source-read-20261011-r1';mode=sys.argv[1];assert mode in ('host','four','off','on')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
serial=0;started=False;finished=False
def call(*args):
    global serial
    serial+=1;sys.argv=['transport',*map(str,args),'--log',str(E/(mode+'-transport-'+str(serial)+'.txt'))]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
def unpack():
    assert call('get',remote+'/return-'+mode+'.tar',E/('return-'+mode+'.tar'))==0
    out=E/(mode+'-return');extract_bytes(E/('return-'+mode+'.tar'),out);d=out/('run-'+mode)
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    return d
def deployment(c):
    assert not c['mock'] and c['sync_start']==0 and c['layers']==11 and c['member_count']==19 and c['forward_calls']==0
    assert [x['value'] for x in c['boundary']]==[486,478,4386,4390] and [x['bytes'] for x in c['boundary']]==[400,17280,30240,16800]
    for i,x in enumerate(c['boundary']):
        assert 104*1024*1024<=x['physical'] and x['physical']+x['bytes']<=105*1024*1024
        assert not x['is_ocm'] and x['alias_from']==[-1,-1,8467,8479][i]
        assert x['physical']>=x['owned_chunk_start'] and x['bytes']<=x['owned_chunk_capacity']-(x['physical']-x['owned_chunk_start'])
    for i,x in enumerate(c['boundary']):
        for y in c['boundary'][i+1:]:assert x['physical']+x['bytes']<=y['physical'] or y['physical']+y['bytes']<=x['physical']
def fnv(b):
    h=14695981039346656037
    for byte in b:h=((h^byte)*1099511628211)&((1<<64)-1)
    return h
try:
    if mode=='host':
        assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote)==0;assert call('put',E/'transfer.tar',remote+'/transfer.tar')==0
        code=call('ssh','set -eu; cd '+remote+'; echo "'+sha(E/'transfer.tar')+'  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_producer_read_check pose_producer_payload_selftest pose_producer_schedule_selftest pose_producer_observer_selftest pose_producer_phase_selftest pose_producer_address_selftest pose_producer_read_selftest pose_producer_read_host_check; python3 board_producer_read_run.py host','--timeout','100')
        d=unpack();assert code==0 and (d/'exit.txt').read_text().strip()=='0';assert (d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes()
        events=[json.loads(x) for x in (d/'observer/events.jsonl').read_text().splitlines()];assert len(events)==4 and [x['return'] for x in events]==[-1,-1,0,0] and [x['errno_at_return'] for x in events]==[4,11,0,33]
        (E/'host.review.json').write_text(json.dumps({'status':'ARM_payload_schedule_observer_contracts_passed','archive_sha256':sha(E/'return-host.tar'),'kernel_unchanged':True,'NPU_calls':0},indent=2)+'\n');print('ARM payload/schedule/ioctl/phase contracts passed; no device initialization')
    else:
        assert json.loads((E/'host.review.json').read_text())['status']=='ARM_payload_schedule_observer_contracts_passed'
        if mode in ('off','on'):assert json.loads((E/'four.phase-review.json').read_text())['calls']==4
        if mode=='on':assert json.loads((E/'off.data-review.json').read_text())['status']=='fixed100_outputs_and_lifecycle_verified'
        launch='cd '+remote+' && python3 -c "import subprocess; from pathlib import Path; assert not Path(\'run-'+mode+'\').exists(); p=subprocess.Popen([\'python3\',\'board_producer_read_run.py\',\''+mode+'\'],stdin=subprocess.DEVNULL,stdout=open(\''+mode+'-manager.stdout.txt\',\'wb\'),stderr=open(\''+mode+'-manager.stderr.txt\',\'wb\'),start_new_session=True); Path(\''+mode+'-manager.pid\').write_text(str(p.pid)+\'\\n\')"'
        assert call('ssh',launch)==0;started=True;gate=False;begin=time.monotonic()
        while time.monotonic()-begin<190:
            local=E/(mode+'-status-'+str(serial+1)+'.json')
            query='cd '+remote+' && python3 -c "import json; from pathlib import Path; Path(\'status-'+mode+'.json\').write_text(json.dumps({\'finished\':Path(\'finished-'+mode+'.json\').exists(),\'ready\':Path(\'run-'+mode+'/results/deployment.ready\').exists()}))"'
            assert call('ssh',query)==0;assert call('get',remote+'/status-'+mode+'.json',local)==0;s=json.loads(local.read_text())
            if s['finished']:finished=True;break
            if s['ready'] and not gate:
                doc=E/(mode+'-deployment.json');ready=E/(mode+'-deployment.ready')
                for name in ('prefix.json','address-map.json'):
                    assert call('get',remote+'/run-'+mode+'/results/'+name,E/(mode+'-'+name))==0
                prefix=json.loads((E/(mode+'-prefix.json')).read_text());layout=json.loads((E/(mode+'-address-map.json')).read_text());assert prefix['prefix_start']==4096 and prefix['prefix_bytes']==104*1024*1024 and prefix['read_write_copy_calls']==0
                blocks=layout['chunks'];assert len({x['identity'] for x in blocks})==len(blocks)
                for i,x in enumerate(blocks):
                    if x['identity']!=prefix['identity']:assert x['address']>=4096+104*1024*1024 and x['address']+x['bytes']<=105*1024*1024
                    for y in blocks[i+1:]:assert x['address']+x['bytes']<=y['address'] or y['address']+y['bytes']<=x['address']
                assert call('get',remote+'/run-'+mode+'/results/deployment.json',doc)==0;deployment(json.loads(doc.read_text()))
                assert call('get',remote+'/run-'+mode+'/results/deployment.ready',ready)==0;assert ready.read_text()==str(fnv(doc.read_bytes()))+'\n'
                memory=E/(mode+'-memory-review');memory.mkdir();ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
                for i in range(2):
                    for v,ext in ((486,'f32'),(478,'f16')):
                        p=memory/(str(i)+'-'+str(v)+'.roundtrip');assert call('get',remote+'/run-'+mode+'/results/memory-pattern-'+str(i)+'/input-'+str(v)+'.roundtrip',p)==0
                        assert p.read_bytes()==(ref/('pattern-'+str(i))/('input-'+str(v)+'.'+ext)).read_bytes()
                (E/(mode+'-deployment.review.json')).write_text(json.dumps({'status':'deployed_scope_and_physical_memory_passed_before_forward','sha256':sha(doc)},indent=2)+'\n')
                assert call('put',ready,remote+'/run-'+mode+'/results/forward.pending')==0
                assert call('ssh','set -eu; test ! -e '+remote+'/run-'+mode+'/results/forward.allow; mv '+remote+'/run-'+mode+'/results/forward.pending '+remote+'/run-'+mode+'/results/forward.allow')==0
                gate=True;print(mode,'fixed100 gate released',flush=True)
            time.sleep(4)
        else:raise RuntimeError('Finite controller deadline exceeded')
        d=unpack();code=int((d/'exit.txt').read_text());report={'exit':code,'gate_released':gate,'archive_sha256':sha(E/('return-'+mode+'.tar')),'kernel_unchanged':(d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes()}
        (E/(mode+'.exit-review.json')).write_text(json.dumps(report,indent=2)+'\n');print(mode,'returned exit',code,flush=True)
        assert code==0 and report['kernel_unchanged'],'Preserve failure; stop remaining runs'
finally:
    if started and not finished:
        call('ssh','cd '+remote+' && python3 -c "from pathlib import Path; Path(\'abort-'+mode+'.request\').write_text(\'controller-error\\n\')"');time.sleep(6)
        if not (E/('return-'+mode+'.tar')).exists():call('get',remote+'/return-'+mode+'.tar',E/('return-'+mode+'.tar'))
    secret='';t.getpass.getpass=prompt
