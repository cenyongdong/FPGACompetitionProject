param([int]$Seconds=150)
$ErrorActionPreference='Stop'
$dir='D:\FPGACompetitionProject\tools\boot-diagnostics\20261002'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rawPath=Join-Path $dir ('com7_'+$stamp+'.bin')
$logPath=Join-Path $dir ('com7_'+$stamp+'.log')
$port=[System.IO.Ports.SerialPort]::new('COM7',115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$port.Handshake=[System.IO.Ports.Handshake]::None
$port.DtrEnable=$false
$port.RtsEnable=$false
$stream=$null
$total=0
try {
 $port.Open()
 $stream=[System.IO.File]::Open($rawPath,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
 $message="READY $(Get-Date -Format o) COM7 115200 8N1 None DTR=False RTS=False; raw=$rawPath"
 $message | Set-Content -LiteralPath $logPath -Encoding utf8
 Write-Output $message
 $timer=[System.Diagnostics.Stopwatch]::StartNew()
 while($timer.Elapsed.TotalSeconds -lt $Seconds) {
  $available=$port.BytesToRead
  if($available -gt 0) {
   $buffer=[byte[]]::new($available)
   $count=$port.Read($buffer,0,$available)
   $stream.Write($buffer,0,$count);$stream.Flush();$total+=$count
   $decoded=[System.Text.Encoding]::UTF8.GetString($buffer,0,$count)
   Add-Content -LiteralPath $logPath -Value ("$(Get-Date -Format o) bytes=$count`n$decoded") -Encoding utf8
   Write-Output $decoded
  }
  Start-Sleep -Milliseconds 100
 }
 Write-Output "COMPLETE bytes=$total"
 Add-Content -LiteralPath $logPath -Value "COMPLETE $(Get-Date -Format o) bytes=$total" -Encoding utf8
} catch {
 $err="ERROR $(Get-Date -Format o) $($_.Exception.Message) bytes=$total"
 Add-Content -LiteralPath $logPath -Value $err -Encoding utf8
 Write-Output $err
} finally {if($port.IsOpen){$port.Close()};$port.Dispose();if($stream){$stream.Dispose()}}
