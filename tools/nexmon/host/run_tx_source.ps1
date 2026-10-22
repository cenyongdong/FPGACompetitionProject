# Compile the existing timing engine from reviewable source in this process.
# No EXE installation, download service, driver/firewall or Wi-Fi modification.
param([Parameter(Mandatory=$true)][string]$JobFile,[Parameter(Mandatory=$true)][string]$OutputDirectory,[switch]$TraceStack)
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
$parent=Split-Path -Parent $JobFile
New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop|Out-Null
$traceOwned=$false;$traceFilter=$null
if($TraceStack){Push-Location -LiteralPath $OutputDirectory}
try {
 Add-Type -Path (Join-Path $parent 'LaptopTx.cs') -ReferencedAssemblies @('System.dll','System.Core.dll','System.Windows.Forms.dll','System.Web.Extensions.dll','System.Management.dll')
 $raw=Get-Content -Raw -LiteralPath $JobFile|ConvertFrom-Json
 $job=[Collections.Generic.Dictionary[string,object]]::new()
 foreach($property in $raw.PSObject.Properties){$job.Add($property.Name,$property.Value)}
 if($TraceStack){
  $traceFilter='nexmon-'+$job['id']
  $filter=@(pktmon filter add $traceFilter -t UDP -p 39031 2>&1)
  if($LASTEXITCODE){throw 'Pktmon filter failed'}
  $trace=@(pktmon start --capture --comp all --pkt-size 128 --flags 0x01B --file-name (Join-Path $OutputDirectory 'stack.etl') --file-size 16 --log-mode memory 2>&1)
  if($LASTEXITCODE){throw 'Pktmon start failed; existing capture was not stopped'}
  $traceOwned=$true
  @{filter=$filter;start=$trace}|ConvertTo-Json -Depth 3|Set-Content (Join-Path $OutputDirectory 'trace-start.json') -Encoding UTF8
 }
 @{pid=$PID;id=$job['id'];ready_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'READY.json') -Encoding UTF8
 $deadline=[Diagnostics.Stopwatch]::StartNew()
 while(-not(Test-Path -LiteralPath (Join-Path $OutputDirectory 'GO'))){
  if($deadline.Elapsed.TotalSeconds -gt 45){throw 'No GO received within bounded armed wait; no TX was released'}
  if(Test-Path -LiteralPath (Join-Path $OutputDirectory 'STOP')){throw 'Cancelled before TX'}
  Start-Sleep -Milliseconds 50
 }
 $result=[LaptopTx]::Transmit($job,$false)
 $result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputDirectory 'sender.json') -Encoding UTF8
}catch{
 @{error=$_.Exception.Message;time_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'error.json') -Encoding UTF8
 exit 1
}finally{
 $ErrorActionPreference='Continue'
 if($traceOwned){
  @(pktmon stop 2>&1)|Set-Content (Join-Path $OutputDirectory 'trace-stop.txt') -Encoding UTF8
  # This Windows build ignores --file-name in memory mode and flushes to
  # PktMon.etl in the caller's working directory. Keep that inside this run.
  $memoryLog=Join-Path $OutputDirectory 'PktMon.etl'
  if(Test-Path -LiteralPath $memoryLog){Move-Item -LiteralPath $memoryLog -Destination (Join-Path $OutputDirectory 'stack.etl') -ErrorAction Stop}
  @(pktmon etl2txt (Join-Path $OutputDirectory 'stack.etl') --out (Join-Path $OutputDirectory 'stack.txt') --hex --metadata 2>&1)|Set-Content (Join-Path $OutputDirectory 'trace-convert.txt') -Encoding UTF8
 }
 # Preflight requires no existing filters; only the single owned filter exists.
 if($traceFilter){@(pktmon filter remove 2>&1)|Set-Content (Join-Path $OutputDirectory 'trace-filter-remove.txt') -Encoding UTF8}
 if($TraceStack){Pop-Location}
}
