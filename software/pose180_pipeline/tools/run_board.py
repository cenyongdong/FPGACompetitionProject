"""One bounded software load; no BOOT writes, reboot, rearm or automatic retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


def owners():
    result=[]
    for fd in Path('/proc').glob('[0-9]*/fd/*'):
        try:
            target=os.readlink(fd)
            if target.startswith(('/dev/axi','/dev/udmabuf','/dev/u-dma','/dev/video')):result.append([str(fd),target])
        except OSError:pass
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--session',type=int,required=True)
    parser.add_argument('--frames',type=int,default=52800)
    parser.add_argument('--hdmi',type=int,choices=(0,1),required=True)
    parser.add_argument('--hard-seconds',type=int,default=2100)
    args=parser.parse_args()
    if not 0<args.frames<=54000 or not args.session or not 60<=args.hard_seconds<=2100:raise ValueError('Invalid finite run budget')
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/'identity.json').read_text())
    for name,digest in manifest['files'].items():
        if sha(root/name)!=digest:raise ValueError('Package identity differs: '+name)
    metadata=root/'metadata';metadata.mkdir()
    subprocess.run([sys.executable,str(root/'preflight.py'),str(metadata/'before-preflight.json')],check=True)
    before=json.loads((metadata/'before-preflight.json').read_text())
    if sorted(before['boot_files'],key=lambda row:row['name'])!=sorted(manifest['protected_original_boot_files'],key=lambda row:row['name']):
        raise ValueError('Protected boot files differ; no SDK initialization')
    if before['SDK_packages']!=['customop arm64 3.39.0','icraft arm64 3.39.0']:
        raise ValueError('SDK package identity differs')
    for name,digest in manifest['SDK_libraries'].items():
        actual=before['libraries'].get(name) or sha(Path('/usr/lib/aarch64-linux-gnu')/name)
        if actual!=digest:raise ValueError('SDK library identity differs: '+name)
    if owners():raise ValueError('Existing device owner; preserve other work')
    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()!='operating':raise ValueError('FPGA is not operating')
    if args.hdmi:
        admission=json.loads((root/'startup-admission.json').read_text())
        if admission.get('boot_id')!=boot_id or admission.get('mode') not in ('healthy','consumed'):
            raise ValueError('A fresh same-boot HDMI startup admission is required')
        if (root/'startup-mode.txt').read_text().strip()!=admission['mode']:raise ValueError('Startup mode differs')
    for name,command in (('before.dmesg',['dmesg']),):
        (metadata/name).write_bytes(subprocess.check_output(command))
    (metadata/'before.meminfo').write_bytes(Path('/proc/meminfo').read_bytes())
    attempt=dict(boot_id=boot_id,frames=args.frames,hdmi=bool(args.hdmi),hard_seconds=args.hard_seconds,
        CSI_live=False,automatic_retry=False,session=args.session)
    # Creating this token prevents a second Session even after a controller crash.
    with (root/'sdk-attempt.json').open('x') as stream:json.dump(attempt,stream,indent=2)
    command=[str(root/'pose180_pipeline'),str(root),str(root/'run'),str(args.frames),str(args.session),'39382',str(args.hdmi)]
    started=time.monotonic();child=None;stop_reason=None
    with (metadata/'native.stdout.log').open('xb') as stdout,(metadata/'native.stderr.log').open('xb') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        process=dict(pid=child.pid,start_ticks=Path('/proc/%d/stat'%child.pid).read_text().split()[21],argv=command,boot_id=boot_id)
        (metadata/'process.json').write_text(json.dumps(process,indent=2)+'\n')
        with (metadata/'resources.jsonl').open('x') as resources:
            while child.poll() is None:
                memory=Path('/proc/meminfo').read_text();status=Path('/proc/%d/status'%child.pid)
                try:process_status=status.read_text()
                except FileNotFoundError:process_status='process exited during resource sample'
                resources.write(json.dumps(dict(elapsed_seconds=time.monotonic()-started,
                    status=process_status,meminfo=memory))+'\n');resources.flush()
                available=next(int(line.split()[1]) for line in memory.splitlines() if line.startswith('MemAvailable:'))
                if time.monotonic()-started>args.hard_seconds:stop_reason='Explicit hard runtime budget exceeded'
                if available<131072:stop_reason='Actual MemAvailable below 128MiB safety floor'
                if Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=boot_id:stop_reason='Runtime boot identity changed'
                if stop_reason:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # This is an explicit hard/safety boundary, not a quiet-log timeout.
                        os.killpg(child.pid,signal.SIGKILL);child.wait()
                    break
                time.sleep(1)
    native=child.wait()
    (metadata/'after.dmesg').write_bytes(subprocess.check_output(['dmesg']))
    (metadata/'after.meminfo').write_bytes(Path('/proc/meminfo').read_bytes())
    subprocess.run([sys.executable,str(root/'preflight.py'),str(metadata/'after-preflight.json')],check=True)
    after=json.loads((metadata/'after-preflight.json').read_text())
    if before['boot_files']!=after['boot_files'] or before['SDK_packages']!=after['SDK_packages']:
        stop_reason=stop_reason or 'Protected boot files or SDK package identity changed'
    for name,digest in manifest['SDK_libraries'].items():
        actual=after['libraries'].get(name) or sha(Path('/usr/lib/aarch64-linux-gnu')/name)
        if actual!=digest:stop_reason=stop_reason or 'SDK library identity changed'
    outcome=dict(native_exit=native,stop_reason=stop_reason,elapsed_seconds=time.monotonic()-started,
        boot_id=boot_id,final_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),device_owners=owners(),
        BOOT_writes=0,reboots=0,CSI_live=False,automatic_retry=False)
    (root/'outcome.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps(outcome))
    return 0 if native==0 and not stop_reason else 1


if __name__=='__main__':raise SystemExit(main())
