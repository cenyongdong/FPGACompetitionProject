"""Finite board manager: public deployment review barrier, no automatic retry."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time,tarfile
root=Path(__file__).resolve().parent;os.chdir(root);mode=sys.argv[1];assert mode in ('mock','physical')
run=root/('run-'+mode);assert not run.exists();run.mkdir();results=run/'results'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(args,target):
    with (run/target).open('wb') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
def snapshot(prefix):
    capture(['dmesg'],prefix+'.dmesg.txt')
    for name in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):(run/(prefix+'.'+name)).write_bytes(Path('/proc/'+name).read_bytes())
child=None;code=1;reason='setup_failed'
try:
    capture(['sha256sum','-c','files.sha256'],'package-check.txt')
    m=json.loads((root/'build-result.json').read_text());assert sha(root/'pose_producer_group_check')==m['program_sha256']
    for n,h in m['libraries'].items():assert sha('/usr/lib/aarch64-linux-gnu/'+n)==h
    graph=Path('/tmp/pose-producer-reference-20261011-r2/models/piw24_ZG.json');raw=graph.with_suffix('.raw')
    assert sha(graph)==m['graph_sha256'] and sha(raw)==m['raw_sha256']
    capture(['python3','board_application_preflight.py',str(run/'preflight.json')],'preflight.stdout.txt')
    p=json.loads((run/'preflight.json').read_text());assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
    assert next(x['sha256'] for x in p['boot_files'] if x['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    assert not any(x.split()[1].startswith('pose_') for x in p['processes'].splitlines()[1:] if len(x.split())>1)
    snapshot('before');capture(['ldd','pose_producer_group_check'],'ldd.txt')
    assert 'not found' not in (run/'ldd.txt').read_text()
    if mode=='mock':capture(['./pose_producer_payload_selftest','patterns'],'payload-arm.txt')
    work=run/'work';work.mkdir()
    args=[str(root/'pose_producer_group_check'),mode,str(graph),str(raw),str(root/'patterns'),str(results),'--mock-only' if mode=='mock' else '--allow-device-init']
    start=time.monotonic();forward_start=None
    with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err:
        child=subprocess.Popen(args,cwd=work,stdout=out,stderr=err,start_new_session=True)
        (run/'child.pid').write_text(str(child.pid)+'\n')
        while child.poll() is None:
            current=time.monotonic()
            if mode=='physical' and (results/'forward.allow').exists() and forward_start is None:forward_start=current
            cancelled=(root/'abort.request').exists()
            expired=cancelled or (current-start>(40 if mode=='mock' else 300) if forward_start is None else current-forward_start>60)
            if expired:
                reason='controller_cancelled' if cancelled else ('external_mock_timeout' if mode=='mock' else ('external_forward_60s_timeout' if forward_start else 'external_deployment_300s_timeout'))
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
                code=124;break
            time.sleep(.1)
        else:code=child.returncode;reason='program_exit'
    (run/'budget.json').write_text(json.dumps({'program_exit':child.returncode,'exit':code,'reason':reason,'elapsed_seconds':time.monotonic()-start,'forward_gate_observed':forward_start is not None})+'\n')
except Exception as e:
    (run/'manager.failure.txt').write_text(repr(e)+'\n')
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
    (run/'exit.txt').write_text(str(code)+'\n')
    snapshot('after');capture(['ps','-eo','pid,comm,args'],'processes.txt');capture(['ss','-ltnp'],'ports.txt')
    with (run/'files.sha256').open('w') as f:
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.name!='files.sha256':f.write(sha(p)+'  '+p.relative_to(run).as_posix()+'\n')
    archive=root/('return-'+mode+'.tar')
    with tarfile.open(archive,'w') as f:f.add(run,arcname=run.name)
    (root/('finished-'+mode+'.json')).write_text(json.dumps({'exit':code,'archive_sha256':sha(archive),'reason':reason})+'\n')
    print(mode,'finished',code,reason,flush=True)
sys.exit(code)
