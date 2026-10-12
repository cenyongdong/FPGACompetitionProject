"""Bounded single demo lifecycle; current identity/resources and complete return."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,tarfile,time,re
root=Path(__file__).resolve().parent;os.chdir(root)
mode=sys.argv[1];assert mode in ('host','short','demo')
run=root/('run-'+mode);assert not run.exists();run.mkdir()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def snap(prefix):
    for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):(run/(prefix+'.'+n)).write_bytes(Path('/proc/'+n).read_bytes())
    (run/(prefix+'.dmesg.txt')).write_bytes(subprocess.check_output(['dmesg']))
def units(path):
    total=0
    for line in path.read_text().splitlines():
        m=re.match(r'Node\s+\d+,\s+zone\s+\w+,\s+type\s+(Unmovable|Movable|Reclaimable)\s+(.*)',line)
        if m:total+=sum(n*(1<<(i-7)) for i,n in enumerate(map(int,m[2].split())) if i>=7)
    return total
code=1;child=None
try:
    m=json.loads((root/'build-result.json').read_text())
    for line in (root/'files.sha256').read_text().splitlines():digest,name=line.split('  ',1);assert sha(root/name)==digest
    for name,h in m['programs'].items():assert sha(root/name)==h
    for name,h in m['libraries'].items():assert sha('/usr/lib/aarch64-linux-gnu/'+name)==h
    assert sha(root/'models/piw24_ZG.json')==m['graph_sha256'] and sha(root/'models/piw24_ZG.raw')==m['raw_sha256']
    subprocess.run(['python3','board_application_preflight.py',str(run/'preflight.json')],check=True,stdout=(run/'preflight.stdout.txt').open('wb'))
    p=json.loads((run/'preflight.json').read_text());assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
    assert next(x['sha256'] for x in p['boot_files'] if x['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    assert not any(x.split()[1].startswith('pose_') for x in p['processes'].splitlines()[1:] if len(x.split())>1)
    snap('before')
    if mode=='host':
        with (run/'transport-arm.txt').open('wb') as f:subprocess.run(['./pose_demo_transport_test','--self-test'],stdout=f,stderr=subprocess.STDOUT,check=True)
        code=0
    else:
        before=units(run/'before.pagetypeinfo');compact=before<16
        start=time.monotonic_ns()
        if compact:Path('/proc/sys/vm/compact_memory').write_text('1\n')
        elapsed=time.monotonic_ns()-start;snap('prepared')
        (run/'resources.json').write_text(json.dumps({'ordinary_units512KiB_before':before,'ordinary_units512KiB_after':units(run/'prepared.pagetypeinfo'),'compactions':int(compact),'elapsed_ns':elapsed,'reason':'Ordinary high-order pages below16 -> one logged preparation; otherwise audit only. Not guaranteed startup.','CMA_changed':False,'drop_caches':False,'reboot':False})+'\n')
        assert units(run/'prepared.pagetypeinfo')>=16,'VPU startup resource preflight refused; compaction did not restore ordinary pages, no device opened'
        frames=3 if mode=='short' else 60
        command=[str(root/'pose_demo'),'--model-dir',str(root/'models'),'--output',str(run/'results'),'--max-frames',str(frames),'--allow-device-init','--allow-vpu-stream','--allow-network']
        with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err:
            child=subprocess.Popen(command,cwd=run,stdout=out,stderr=err,start_new_session=True);begin=time.monotonic()
            (run/'child.pid').write_text(str(child.pid)+'\n')
            while child.poll() is None:
                if time.monotonic()-begin>180 or (root/('abort-'+mode)).exists():
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
                    code=124;break
                time.sleep(.1)
            else:code=child.returncode
        (run/'budget.json').write_text(json.dumps({'exit':code,'seconds':time.monotonic()-begin,'hardware_budget_seconds':180})+'\n')
except Exception as e:(run/'manager.failure.txt').write_text(repr(e)+'\n')
finally:
    if child and child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
    snap('after');(run/'exit.txt').write_text(str(code)+'\n')
    (run/'processes.txt').write_bytes(subprocess.check_output(['ps','-eo','pid,comm,args']))
    (run/'ports.txt').write_bytes(subprocess.check_output(['ss','-ltnp']))
    with (run/'files.sha256').open('w') as f:
        for p in sorted(run.rglob('*')):
            if p.is_file() and p.name!='files.sha256':f.write(sha(p)+'  '+p.relative_to(run).as_posix()+'\n')
    with tarfile.open(root/('return-'+mode+'.tar'),'w') as t:t.add(run,arcname=run.name)
    (root/('finished-'+mode+'.json')).write_text(json.dumps({'exit':code,'archive_sha256':sha(root/('return-'+mode+'.tar'))})+'\n')
    print('Demo',mode,'finished',code)
sys.exit(code)
