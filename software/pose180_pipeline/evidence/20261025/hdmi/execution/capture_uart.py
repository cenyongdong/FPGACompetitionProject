from pathlib import Path
import json,subprocess,sys,time

E=Path(__file__).resolve().parent

tag=sys.argv[1]
if tag not in ('candidate-1','fallback'):raise ValueError('Unknown bounded capture')
out=E/('uart-'+tag)
if out.exists():raise RuntimeError('Preserve earlier UART capture')
script=Path(__file__).with_name('capture_hdmi_startup.ps1').read_text(encoding='utf-8-sig')
lines=script.splitlines()
lines[1]="$taskOut = '"+out.as_posix()+"'"
identity=r'''$taskUsbKey = 'HKLM:\SYSTEM\CurrentControlSet\Enum\USB\VID_10C4&PID_EA60\0001'
$taskUsb = Get-ItemProperty -LiteralPath $taskUsbKey
$taskUsbPort = Get-ItemProperty -LiteralPath ($taskUsbKey+'\Device Parameters')
if ($taskUsbPort.PortName -ine 'COM7' -or $taskUsb.FriendlyName -notlike 'Silicon Labs CP210x*(COM7)*') {throw 'Verified CP210x COM7 identity changed'}'''
script='\n'.join(lines).replace('$taskPort = New-Object',identity+'\n$taskPort = New-Object',1)
path=E/('uart-'+tag+'-reader.ps1');path.write_text(script,encoding='utf-8-sig')
with (E/('uart-'+tag+'-reader.stdout.log')).open('xb') as so,(E/('uart-'+tag+'-reader.stderr.log')).open('xb') as se:
 p=subprocess.Popen(['powershell.exe','-NoProfile','-File',str(path)],stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
 (E/('uart-'+tag+'-process.json')).write_text(json.dumps(dict(pid=p.pid,script=str(path),TX_bytes=0,seconds_budget=300,bytes_budget=4194304),indent=2))
 while not (out/'ready.json').exists() and p.poll() is None:time.sleep(.05)
 if not (out/'ready.json').exists():raise RuntimeError('Serial did not open; do not install/reboot')
 ready=json.loads((out/'ready.json').read_text(encoding='utf-8-sig'))
 if not ready['opened']:raise RuntimeError('Serial did not open')
 print(json.dumps(dict(UART_CAPTURE_READY=True,pid=p.pid,directory=str(out),TX_bytes=0)),flush=True)
 while p.poll() is None:
  try:p.wait(timeout=30)
  except subprocess.TimeoutExpired:print(json.dumps(dict(capture=tag,pid=p.pid,received_bytes=(out/'rx.bin').stat().st_size)),flush=True)
result=json.loads((out/'reader.json').read_text(encoding='utf-8-sig'))
print(json.dumps(result),flush=True)
if p.returncode or result.get('error') or not result.get('closed'):raise SystemExit('Capture error retained; inspect before further boot')
