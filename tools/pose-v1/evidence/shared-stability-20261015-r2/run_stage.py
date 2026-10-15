"""Finite board controller: identity checks, bounded /proc sampling, stop and preserve."""
from pathlib import Path
import argparse,hashlib,json,os,signal,subprocess,sys,time,traceback
import board_run as common

def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def fields(p):
    result={}
    for line in p.read_text().splitlines():
        k,_,v=line.partition(':')
        try:result[k]=int(v.strip().split()[0])
        except (ValueError,IndexError):pass
    return result
def sample(pid):
    root=Path('/proc')/str(pid);status=fields(root/'status');smaps=fields(root/'smaps_rollup')
    child_file=root/'task'/str(pid)/'children'
    try:
        children=child_file.read_text().strip();children_supported=True
    except FileNotFoundError:
        if not root.exists():raise
        children=None;children_supported=False
    return dict(pid=pid,status_kb=status,smaps_kb=smaps,fd_count=len(list((root/'fd').iterdir())),
                map_count=len((root/'maps').read_text().splitlines()),
                children=children,children_observation_supported=children_supported)

def verify(root,run,package,post=False):
    for n,h in package['files'].items():
        if common.sha(root/n)!=h:raise RuntimeError('Package identity differs: '+n)
    for n,h in package['libraries'].items():
        if common.sha(Path('/usr/lib/aarch64-linux-gnu')/n)!=h:raise RuntimeError('SDK library identity differs: '+n)
    for n,h in package['sdk_headers_normalized_sha256'].items():
        if hashlib.sha256((Path('/usr/include')/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=h:
            raise RuntimeError('SDK header identity differs: '+n)
    out=run/('post-preflight.json' if post else 'preflight.json')
    subprocess.run([sys.executable,str(root/'board_application_preflight.py'),str(out)],check=True,timeout=30)
    pf=load(out)
    if pf['boot_files']!=package['expected_boot_files'] or pf['fpga_state']!='operating':raise RuntimeError('BOOT/FPGA identity differs')
    if pf['SDK_packages']!=['customop arm64 3.39.0','icraft arm64 3.39.0']:raise RuntimeError('SDK package version differs')
    if not post and any(len(s.split())>1 and s.split()[1].startswith('pose_') for s in pf['processes'].splitlines()[1:]):
        raise RuntimeError('Existing pose process; preserve other work')
    return pf

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=('basic','short','stress'),required=True)
    a=ap.parse_args();root=Path(__file__).resolve().parent;plan=load(root/'plan.json')[a.stage]
    run=root/('run-'+a.stage);run.mkdir();child=None;code=1;reason='';monitor_failure=None;baseline=None
    started=time.monotonic();last_kernel_check=started;shutdown=False
    def interrupted(signum,frame):raise KeyboardInterrupt('Controller interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        common.snapshot(run,'before');package=load(root/'package.json');before=verify(root,run,package)
        expected=package['expected_linux_version'].encode()
        if expected not in (run/'before.dmesg.txt').read_bytes():raise RuntimeError('Kernel identity differs')
        if a.stage=='basic':
            cmd=[str(root/'pose_shared_timing'),'--package',str(root),'--output',str(run/'results'),
                 '--mode','wall','--cycles','1','--allow-device-init']
        else:
            if a.stage=='stress':
                short=root/'run-short'
                if (short/'exit.txt').read_text().strip()!='0':raise RuntimeError('Short validation did not pass')
                audit=load(root/'short-reviewed.json')
                if not audit['approved_to_start_stress']:raise RuntimeError('Short stage not reviewed')
            if (root/'run-basic/exit.txt').read_text().strip()!='0':raise RuntimeError('Compiled package basic validation did not pass')
            cmd=[str(root/'pose_shared_resident'),'--package',str(root),'--output',str(run/'results'),
                 '--seconds',str(plan['seconds']),'--max-frames',str(plan['max_frames']),'--allow-device-init']
        save(run/'command.json',dict(argv=cmd,plan=plan))
        with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err,(run/'resources.jsonl').open('w') as samples:
            child=subprocess.Popen(cmd,stdout=out,stderr=err,start_new_session=True)
            (run/'child.pid').write_text(str(child.pid));last_progress=time.monotonic();last_done=-1;initialized_at=None
            while child.poll() is None:
                now=time.monotonic()
                if now-started>plan['wall_timeout_seconds']:raise TimeoutError('Stage wall timeout; no retry')
                init=run/'results/initialized.json';progress=run/'results/progress.json'
                if init.exists() and initialized_at is None:initialized_at=now;last_progress=now
                if progress.exists():
                    state=load(progress)
                    if state['completed']!=last_done:last_progress=now;last_done=state['completed']
                if initialized_at is not None and now-last_progress>20:raise TimeoutError('Inference progress stalled >20s')
                if initialized_at is None and a.stage!='basic' and now-started>100:raise TimeoutError('Engine initialization exceeded100s')
                try:r=sample(child.pid)
                except (FileNotFoundError,ProcessLookupError):
                    if child.poll() is not None:break
                    raise
                mem=fields(Path('/proc/meminfo'));free=os.statvfs(root).f_bavail*os.statvfs(root).f_frsize
                r.update(monotonic_s=now,elapsed_s=now-started,initialized=initialized_at is not None,
                    inference_elapsed_s=None if initialized_at is None else now-initialized_at,
                    completed=last_done,meminfo_kb=mem,disk_free_bytes=free)
                samples.write(json.dumps(r)+'\n');samples.flush()
                rss=r['status_kb'].get('VmRSS',0)
                if rss>524288 or mem['MemAvailable']<98304 or free<2147483648:
                    raise RuntimeError('Resource safety cap exceeded: RSS512MiB/MemAvailable96MiB/disk2GiB')
                if initialized_at is not None and now-initialized_at>=plan['memory_warmup_seconds']:
                    if baseline is None:baseline=r
                    if rss>baseline['status_kb'].get('VmRSS',0)+65536:raise RuntimeError('RSS grew >64MiB after warmup')
                    if r['fd_count']>baseline['fd_count']+16 or r['status_kb']['Threads']>baseline['status_kb']['Threads']+8:
                        raise RuntimeError('FD/thread growth safety cap exceeded')
                if now-last_kernel_check>=5:
                    kernel=subprocess.check_output(['dmesg'])
                    if kernel!=(run/'before.dmesg.txt').read_bytes():raise RuntimeError('Kernel log changed; stop')
                    last_kernel_check=now
                time.sleep(.5)
            code=child.wait()
        if code==0 and (run/'stderr.txt').stat().st_size:raise RuntimeError('Unexpected stderr')
        if code!=0:reason='Child failed; preserve original error, do not retry'
    except BaseException as error:
        reason=str(error);monitor_failure=dict(error=str(error),traceback=traceback.format_exc())
        if child and child.poll() is None:common.stop_child(child);shutdown=True
        code=code if code else 1
    finally:
        if child and child.poll() is None:common.stop_child(child);shutdown=True
        try:
            common.snapshot(run,'after');post=verify(root,run,load(root/'package.json'),post=True)
            if (run/'before.dmesg.txt').read_bytes()!=(run/'after.dmesg.txt').read_bytes():
                code=code if code else 1;reason+='; kernel log changed'
        except Exception as e:
            code=code if code else 1;reason+='; final audit: '+str(e)
        if monitor_failure:save(run/'monitor-failure.json',monitor_failure)
        (run/'exit.txt').write_text(str(code)+'\n')
        save(run/'controller-summary.json',dict(exit=code,reason=reason,elapsed_seconds=time.monotonic()-started,
            killed_child=shutdown,graceful_engine_cleanup_verified=not shutdown and code==0,automatic_retry=False))
        hashes={p.relative_to(run).as_posix():common.sha(p) for p in sorted(run.rglob('*')) if p.is_file()}
        save(run/'evidence-files.json',hashes)
    return code
if __name__=='__main__':raise SystemExit(main())
