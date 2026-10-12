"""Bounded off/on board manager with no retry; same binary and fixed100."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time,tarfile
root=Path(__file__).resolve().parent;os.chdir(root);mode=sys.argv[1];assert mode in ('host','off','on')
run=root/('run-'+mode);assert not run.exists();run.mkdir();results=run/'results';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(args,name):
    with (run/name).open('wb') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
def snap(prefix):
    capture(['dmesg'],prefix+'.dmesg.txt')
    for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):(run/(prefix+'.'+n)).write_bytes(Path('/proc/'+n).read_bytes())
child=None;code=1;reason='setup_failed'
try:
    capture(['sha256sum','-c','files.sha256'],'package-check.txt');m=json.loads((root/'build-result.json').read_text())
    assert sha(root/'pose_producer_vpu_check')==m['program_sha256']
    for n,h in m['libraries'].items():assert sha('/usr/lib/aarch64-linux-gnu/'+n)==h
    graph=Path('/tmp/pose-producer-reference-20261011-r2/models/piw24_ZG.json');raw=graph.with_suffix('.raw');assert sha(graph)==m['graph_sha256'] and sha(raw)==m['raw_sha256']
    capture(['python3','board_application_preflight.py',str(run/'preflight.json')],'preflight.stdout.txt');p=json.loads((run/'preflight.json').read_text())
    assert p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0'] and p['fpga_state']=='operating'
    assert next(x['sha256'] for x in p['boot_files'] if x['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    assert not any(x.split()[1].startswith('pose_') for x in p['processes'].splitlines()[1:] if len(x.split())>1)
    snap('before')
    if mode=='host':
        capture(['./pose_producer_payload_selftest','patterns'],'payload-arm.txt');capture(['./pose_producer_schedule_selftest'],'schedule-arm.txt');capture(['./pose_producer_observer_selftest',str(run/'observer')],'observer-arm.txt');code=0;reason='host_contracts_passed'
    else:
        work=run/'work';work.mkdir();start=time.monotonic();forward_start=None
        with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err:
            child=subprocess.Popen([str(root/'pose_producer_vpu_check'),mode,str(graph),str(raw),str(root/'patterns'),str(results),'--allow-device-init'],cwd=work,stdout=out,stderr=err,start_new_session=True)
            (run/'child.pid').write_text(str(child.pid)+'\n')
            while child.poll() is None:
                t=time.monotonic()
                if (results/'forward.allow').exists() and forward_start is None:forward_start=t
                cancelled=(root/('abort-'+mode+'.request')).exists()
                expired=cancelled or t-start>180 or (forward_start is not None and t-forward_start>60)
                if expired:
                    reason='controller_cancelled' if cancelled else 'bounded_stage_timeout';os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
                    code=124;break
                time.sleep(.1)
            else:code=child.returncode;reason='program_exit'
        (run/'budget.json').write_text(json.dumps({'exit':code,'reason':reason,'seconds':time.monotonic()-start,'forward_gate_observed':forward_start is not None})+'\n')
except Exception as e:(run/'manager.failure.txt').write_text(repr(e)+'\n')
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
    (run/'exit.txt').write_text(str(code)+'\n');snap('after');capture(['ps','-eo','pid,comm,args'],'processes.txt');capture(['ss','-ltnp'],'ports.txt')
    with (run/'files.sha256').open('w') as f:
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.name!='files.sha256':f.write(sha(p)+'  '+p.relative_to(run).as_posix()+'\n')
    archive=root/('return-'+mode+'.tar')
    with tarfile.open(archive,'w') as f:f.add(run,arcname=run.name)
    (root/('finished-'+mode+'.json')).write_text(json.dumps({'exit':code,'archive_sha256':sha(archive),'reason':reason})+'\n')
    print(mode,'finished',code,reason,flush=True)
sys.exit(code)
