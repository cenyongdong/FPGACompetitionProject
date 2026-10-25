"""One software-only resident trial. No BOOT, reboots, retry or forced SDK kill."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def owners():
    found=[]
    for fd in Path('/proc').glob('[0-9]*/fd/*'):
        try:
            name=os.readlink(fd)
            if name.startswith(('/dev/axi','/dev/udmabuf','/dev/u-dma','/dev/video')):found.append([str(fd),name])
        except OSError:pass
    return found

def main():
    root=Path(__file__).resolve().parent;identity=json.loads((root/'identity.json').read_text())
    for name,digest in identity['files'].items():
        if sha(root/name)!=digest:raise ValueError('Resident package identity differs: '+name)
    for name,digest in identity['model_files'].items():
        if sha(Path(identity['model_package'])/name)!=digest:raise ValueError('Model identity differs: '+name)
    metadata=root/'metadata';metadata.mkdir()
    subprocess.run([sys.executable,str(root/'preflight.py'),str(metadata/'before.json')],check=True)
    before=json.loads((metadata/'before.json').read_text())
    if sorted(before['boot_files'],key=lambda x:x['name'])!=sorted(identity['boot_files'],key=lambda x:x['name']):raise ValueError('Original BOOT identity differs')
    if before['fpga_state']!='operating' or before['SDK_packages']!=['customop arm64 3.39.0','icraft arm64 3.39.0']:raise ValueError('FPGA/SDK differs')
    for name,digest in identity['libraries'].items():
        if sha(Path('/usr/lib/aarch64-linux-gnu')/name)!=digest:raise ValueError('SDK library differs: '+name)
    if owners():raise ValueError('Existing device owner')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if boot!=identity['boot_id']:raise ValueError('Runtime boot changed')
    with (root/'sdk-attempt.json').open('x') as f:json.dump(dict(boot_id=boot,SDK_attempts=1,hdmi=False,CSI_live=False,seconds=90),f)
    command=[str(root/'pose180_demo'),'--package',identity['model_package'],'--output',str(root/'run'),
        '--bind','0.0.0.0','--session',str(identity['session']),'--seconds','90','--hdmi','0']
    started=time.monotonic();reason=None;sent_stop=False
    (metadata/'before.dmesg').write_bytes(subprocess.check_output(['dmesg']))
    with (metadata/'native.stdout.log').open('xb') as out,(metadata/'native.stderr.log').open('xb') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err)
        (metadata/'process.json').write_text(json.dumps(dict(pid=child.pid,start_ticks=Path('/proc/%d/stat'%child.pid).read_text().split()[21],argv=command)))
        print('RESIDENT_LAUNCHED pid=%d'%child.pid,flush=True)
        with (metadata/'resources.jsonl').open('x') as log:
            while child.poll() is None:
                memory=Path('/proc/meminfo').read_text()
                try:status=Path('/proc/%d/status'%child.pid).read_text()
                except FileNotFoundError:break
                log.write(json.dumps(dict(elapsed=time.monotonic()-started,status=status,meminfo=memory))+'\n');log.flush()
                available=next(int(x.split()[1]) for x in memory.splitlines() if x.startswith('MemAvailable:'))
                if available<131072:reason='MemAvailable below 128 MiB'
                if time.monotonic()-started>120:reason=reason or 'Requested stop after 120 seconds; observing existing SDK call'
                if reason and not sent_stop:child.send_signal(signal.SIGTERM);sent_stop=True;print(reason,flush=True)
                # A monitoring deadline never implies SDK quiescence or permits kill/retry.
                time.sleep(1)
    native=child.wait();(metadata/'after.dmesg').write_bytes(subprocess.check_output(['dmesg']))
    outcome=dict(native_exit=native,seconds=time.monotonic()-started,reason=reason,device_owners=owners(),
        boot_id=boot,final_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),SDK_attempts=1,BOOT_writes=0,reboots=0,hdmi=False,CSI_live=False)
    (root/'outcome.json').write_text(json.dumps(outcome,indent=2));print(json.dumps(outcome),flush=True)
    return native

if __name__=='__main__':raise SystemExit(main())
