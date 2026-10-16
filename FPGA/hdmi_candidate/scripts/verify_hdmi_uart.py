"""Verify PS-console RX with a bounded marker; no UART input, SDK or reboot."""
from pathlib import Path
import json
import shlex
import subprocess
import sys
import time
import shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1'
D = E / 'uart-marker-r2'
D.mkdir(exist_ok=False)
marker = 'HDMI_PS_UART_RX_20261016_R2'
reader = r'''
$taskOut='@@OUT@@'
$taskPort=New-Object System.IO.Ports.SerialPort('COM7',115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$taskPort.DtrEnable=$false;$taskPort.RtsEnable=$false
$taskPort.Handshake=[System.IO.Ports.Handshake]::None
$taskBytes=New-Object System.Collections.Generic.List[byte]
$taskResult=[ordered]@{port='COM7';baud=115200;framing='8N1';dtr=$false;rts=$false;transmitted_bytes=0;opened=$false}
try {
 $taskPort.Open();$taskResult.opened=$true
 [IO.File]::WriteAllText((Join-Path $taskOut 'ready.txt'),'open')
 $taskWatch=[Diagnostics.Stopwatch]::StartNew()
 while($taskWatch.Elapsed.TotalSeconds -lt 15) {
  $taskCount=$taskPort.BytesToRead
  if($taskCount -gt 0) {
   $taskBuffer=New-Object byte[] $taskCount
   $taskRead=$taskPort.Read($taskBuffer,0,$taskCount)
   for($taskIndex=0;$taskIndex -lt $taskRead;$taskIndex++) {$taskBytes.Add($taskBuffer[$taskIndex])}
  }
  Start-Sleep -Milliseconds 50
 }
 $taskResult.capture_seconds=$taskWatch.Elapsed.TotalSeconds
} catch {$taskResult.error=$_.Exception.Message}
finally {
 if($taskPort.IsOpen) {$taskPort.Close()};$taskPort.Dispose()
 [IO.File]::WriteAllBytes((Join-Path $taskOut 'rx.bin'),$taskBytes.ToArray())
 $taskResult.closed=$true;$taskResult.received_bytes=$taskBytes.Count
 $taskResult|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskOut 'reader.json') -Encoding UTF8
}
'''.replace('@@OUT@@', str(D))
(D / 'reader.ps1').write_text(reader, encoding='utf-8-sig')
start = time.monotonic()
with (D / 'reader-stdout.txt').open('wb') as out, (D / 'reader-stderr.txt').open('wb') as err:
    proc = subprocess.Popen(['powershell.exe', '-NoProfile', '-File', str(D / 'reader.ps1')],
                            stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline = time.monotonic() + 5
        while not (D / 'ready.txt').exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert (D / 'ready.txt').exists(), 'UART reader did not open; do not emit marker'
        code = ("import os,pathlib;assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()=="
                "'8974fbf7-cbe9-4fc9-954d-4682c45b045f';"
                "fd=os.open('/dev/ttyPS0',os.O_WRONLY|os.O_NOCTTY|os.O_NONBLOCK);"
                "n=os.write(fd,b'\\r\\n" + marker + "\\r\\n');os.close(fd);print('PS_CONSOLE_MARKER_BYTES',n)")
        (D / 'remote-code.py').write_text(code, encoding='utf-8')
        remote = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh',
                                 'python3 -c ' + shlex.quote(code), '--timeout', '10', '--log', str(D / 'ssh.txt')],
                                capture_output=True, timeout=15)
        (D / 'ssh-stdout.txt').write_bytes(remote.stdout)
        (D / 'ssh-stderr.txt').write_bytes(remote.stderr)
        proc.wait(timeout=20)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
reader_result = json.loads((D / 'reader.json').read_text(encoding='utf-8-sig'))
rx = (D / 'rx.bin').read_bytes()
result = {'reader_exit': proc.returncode, 'ssh_exit': remote.returncode,
          'seconds': time.monotonic() - start, 'reader': reader_result,
          'marker': marker, 'marker_received': marker.encode() in rx,
          'Linux_console': '/dev/ttyPS0', 'serial_input_sent': False,
          'BOOT_reboot_SDK_or_register_operation': False}
(D / 'review.json').write_text(json.dumps(result, indent=2) + '\n')
shutil.copyfile(Path(__file__), D / Path(__file__).name)
print(json.dumps(result, indent=2))
assert remote.returncode == 0 and proc.returncode == 0 and result['marker_received'], 'UART link not verified; preserve evidence'
