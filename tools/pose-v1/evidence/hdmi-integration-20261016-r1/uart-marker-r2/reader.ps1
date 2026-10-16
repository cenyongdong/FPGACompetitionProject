
$taskOut='D:\FPGACompetitionProject\tools\pose-v1\evidence\hdmi-integration-20261016-r1\uart-marker-r2'
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
