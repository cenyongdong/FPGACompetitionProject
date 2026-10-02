[CmdletBinding()]
param([string]$ProciseRoot = 'C:\FudanMicro\Procise')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $projectRoot ('runs\build_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 6))
if ($runDir -match '[^\x00-\x7F]') { throw 'Procise requires an ASCII-only project path.' }
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'rtl\lite_led_chaser.v'), (Join-Path $projectRoot 'constraints\lite_led_chaser.fdc'), (Join-Path $PSScriptRoot 'build.tcl') -Destination $runDir
$env:PATH = (Join-Path $ProciseRoot 'dll') + ';' + $env:PATH
$env:APP_DIR = $ProciseRoot
$env:TCL_LIBRARY = Join-Path $ProciseRoot 'tcl8.4'
$env:ICTIME_HOME = $ProciseRoot
$env:FMSH_DB = Join-Path $ProciseRoot 'db'
Write-Output "Build directory: $runDir"
$job = Start-Process -FilePath (Join-Path $ProciseRoot 'bin\procise.exe') -ArgumentList 'build.tcl' -WorkingDirectory $runDir -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $runDir 'procise.stdout.log') -RedirectStandardError (Join-Path $runDir 'procise.stderr.log')
$bitstream = Join-Path $runDir 'rundir\lite_led_chaser.bit'
$bitgenReport = Join-Path $runDir 'rundir\lite_led_chaser.bgn'
if ($job.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $bitstream) -or -not (Test-Path -LiteralPath $bitgenReport)) {
    throw "Native Procise build failed or expected artifacts are missing. Exit code: $($job.ExitCode); inspect $runDir"
}
Write-Output "BUILD_ARTIFACTS_GENERATED: $bitstream"
Write-Output 'Inspect native timing, pin/IO constraints, INIT and bitgen reports before programming.'
