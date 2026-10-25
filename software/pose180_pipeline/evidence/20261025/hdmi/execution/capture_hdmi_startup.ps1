$ErrorActionPreference = 'Stop'
$taskOut = 'D:\FPGACompetitionProject\tools\pose-v1\evidence\hdmi-board-candidate-20261016-r1\uart-startup'
New-Item -ItemType Directory -Path $taskOut -ErrorAction Stop | Out-Null
$taskPort = New-Object System.IO.Ports.SerialPort('COM7',115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$taskPort.DtrEnable = $false
$taskPort.RtsEnable = $false
$taskPort.Handshake = [System.IO.Ports.Handshake]::None
$taskResult = [ordered]@{port='COM7';baud=115200;framing='8N1';dtr=$false;rts=$false;transmitted_bytes=0;opened=$false;pid=$PID;byte_budget=4194304;seconds_budget=300;received_bytes=0;started=(Get-Date).ToString('o')}
$taskStream = [IO.File]::Open((Join-Path $taskOut 'rx.bin'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try {
    $taskPort.Open()
    $taskResult.opened = $true
    $taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'ready.json') -Encoding UTF8
    $taskWatch = [Diagnostics.Stopwatch]::StartNew()
    while ($taskWatch.Elapsed.TotalSeconds -lt 300 -and $taskResult.received_bytes -lt 4194304 -and -not (Test-Path -LiteralPath (Join-Path $taskOut 'stop'))) {
        $taskCount = [Math]::Min($taskPort.BytesToRead,4194304-$taskResult.received_bytes)
        if ($taskCount -gt 0) {
            $taskBuffer = New-Object byte[] $taskCount
            $taskRead = $taskPort.Read($taskBuffer,0,$taskCount)
            $taskStream.Write($taskBuffer,0,$taskRead)
            $taskStream.Flush()
            $taskResult.received_bytes += $taskRead
        }
        Start-Sleep -Milliseconds 50
    }
    $taskResult.capture_seconds = $taskWatch.Elapsed.TotalSeconds
    $taskResult.stopped_on_request = Test-Path -LiteralPath (Join-Path $taskOut 'stop')
} catch {
    $taskResult.error = $_.Exception.Message
} finally {
    if ($taskPort.IsOpen) {$taskPort.Close()}
    $taskPort.Dispose()
    $taskStream.Dispose()
    $taskResult.closed = $true
    $taskResult.finished = (Get-Date).ToString('o')
    $taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'reader.json') -Encoding UTF8
}
$taskResult | ConvertTo-Json
