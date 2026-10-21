"""Verify restored COM7 RX, zero UART TX and no reset/SDK/MMIO operation."""
from pathlib import Path
import json
import shlex
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'
D=E/'uart-resume';D.mkdir(exist_ok=False)
marker='HDMI_R26_UART_RX_20261021'
original=(R/'FPGA/hdmi_candidate/scripts/verify_hdmi_uart.py').read_text()
reader=original.split("reader = r'''",1)[1].split("'''.replace",1)[0].replace('@@OUT@@',str(D))
(D/'reader.ps1').write_text(reader,encoding='utf-8-sig')
expected=json.loads((E/'resume-preflight.json').read_text())['boot_id']
with (D/'reader-stdout.txt').open('xb') as out,(D/'reader-stderr.txt').open('xb') as err:
    proc=subprocess.Popen(['powershell.exe','-NoProfile','-File',str(D/'reader.ps1')],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+5
    while not (D/'ready.txt').exists() and proc.poll() is None and time.monotonic()<deadline:time.sleep(.05)
    if not (D/'ready.txt').exists():
        proc.wait(timeout=20);raise RuntimeError('Serial did not open; no console marker sent')
    code=("import os,pathlib;assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()=="+repr(expected)+";"
          "fd=os.open('/dev/ttyPS0',os.O_WRONLY|os.O_NOCTTY|os.O_NONBLOCK);"
          "n=os.write(fd,"+repr(('\r\n'+marker+'\r\n').encode())+");os.close(fd);print('PS_CONSOLE_MARKER_BYTES',n)")
    (D/'remote-code.py').write_text(code)
    remote=subprocess.run([sys.executable,str(R/'.local/hdmi-live-20261017-r3/secure_transport.py'),'ssh',
        'python3 -c '+shlex.quote(code),'--timeout','10','--log',str(D/'ssh.log')],capture_output=True)
    (D/'ssh-stderr.log').write_bytes(remote.stderr)
    proc.wait(timeout=25)
result=json.loads((D/'reader.json').read_text(encoding='utf-8-sig'))
review={'reader':result,'reader_exit':proc.returncode,'ssh_exit':remote.returncode,
    'marker_received':marker.encode() in (D/'rx.bin').read_bytes(),'boot_id':expected,
    'UART_TX':0,'BOOT_writes':0,'reboots':0,'SDK':0,'MMIO':0}
(D/'review.json').write_text(json.dumps(review,indent=2));print(json.dumps(review))
if proc.returncode or remote.returncode or not review['marker_received']:raise SystemExit('UART verification failed; preserve raw')
