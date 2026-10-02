[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BuildDir,
    [string]$CableSerial = '210512180081',
    [string]$ProciseRoot = 'C:\FudanMicro\Procise',
    [switch]$Program
)
$ErrorActionPreference = 'Stop'
$buildRoot = (Resolve-Path -LiteralPath $BuildDir).Path
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($CableSerial -notmatch '^\d+$') { throw 'This test expects the confirmed numeric cable serial.' }
$review = Get-Content -LiteralPath (Join-Path $buildRoot 'build-review.json') -Raw | ConvertFrom-Json
$bit = Join-Path $buildRoot 'rundir\lite_led_chaser.bit'
function Get-Sha256([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
if ($review.status -ne 'reviewed_for_jtag_download' -or $review.device -ne 'JFMQL30TAI676H' -or $review.startup_clock -ne 'JtagClk') { throw 'Missing native review.' }
if ([IO.Path]::GetFullPath($bit) -ne $review.bitstream -or (Get-Sha256 $bit) -ne $review.bitstream_sha256) { throw 'Bitstream changed after review.' }
if ((Get-Sha256 (Join-Path $projectRoot 'rtl\lite_led_chaser.v')) -ne $review.rtl_sha256) { throw 'RTL changed after review.' }
function Assert-ReviewedIpSources {
    $manifestPath = Join-Path $projectRoot 'source-manifest.json'
    if ((Get-Sha256 $manifestPath) -ne $review.source_manifest_sha256) { throw 'IP manifest changed after review.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $manifest.design_sources) {
        $reviewedHash = $review.design_source_sha256.PSObject.Properties[$entry.stage_name].Value
        if ($reviewedHash -ne $entry.sha256 -or
            (Get-Sha256 (Join-Path $projectRoot $entry.path)) -ne $reviewedHash -or
            (Get-Sha256 (Join-Path $buildRoot $entry.stage_name)) -ne $reviewedHash) {
            throw "IP/design source changed after review: $($entry.path)"
        }
    }
    if ((Get-Sha256 (Join-Path $projectRoot $manifest.xci.path)) -ne $manifest.xci.sha256) { throw 'XCI changed after review.' }
}
Assert-ReviewedIpSources
$programDir = Join-Path $buildRoot ('jtag_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $programDir | Out-Null
$scanTcl = @"
get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number $CableSerial} result]} {
    puts "CHAIN_SCAN_FAIL `$result"
    exit 1
}
puts "CHAIN_SCAN_COMPLETED"
exit
"@
[IO.File]::WriteAllText((Join-Path $programDir 'scan.tcl'), $scanTcl, [Text.Encoding]::ASCII)
$env:PATH = (Join-Path $ProciseRoot 'dll') + ';' + $env:PATH
$env:APP_DIR = $ProciseRoot
$env:TCL_LIBRARY = Join-Path $ProciseRoot 'tcl8.4'
$env:ICTIME_HOME = $ProciseRoot
$env:FMSH_DB = Join-Path $ProciseRoot 'db'
function Invoke-NativeTcl([string]$Name) {
    $job = Start-Process -FilePath (Join-Path $ProciseRoot 'bin\procise.exe') -ArgumentList ($Name + '.tcl') -WorkingDirectory $programDir -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $programDir ($Name + '.stdout.log')) -RedirectStandardError (Join-Path $programDir ($Name + '.stderr.log'))
    if ($job.ExitCode -ne 0) { throw "Native $Name failed. See $programDir" }
}
Invoke-NativeTcl 'scan'
$scan = Get-Content -LiteralPath (Join-Path $programDir 'scan.stdout.log') -Raw
if ($scan -notmatch '1 cable is connected' -or $scan -notmatch "serial number : $CableSerial" -or
    $scan -notmatch '0x9372c093' -or $scan -notmatch 'part_name:\s+jfmql30\s+part_id:\s+0' -or
    $scan -notmatch 'part_name:\s+ps_dap\s+part_id:\s+1' -or $scan -notmatch 'CHAIN_SCAN_COMPLETED' -or
    (Get-Item -LiteralPath (Join-Path $programDir 'scan.stderr.log')).Length -ne 0) {
    throw 'Unexpected hardware chain. Download stopped.'
}
Write-Output "CONFIRMED_CHAIN: jfmql30 part 0; ps_dap part 1; cable $CableSerial"
if (-not $Program) { Write-Output "Scan only. Logs: $programDir"; return }
if ((Get-Sha256 $bit) -ne $review.bitstream_sha256) { throw 'Bitstream changed before download.' }
Assert-ReviewedIpSources
$tclBit = $bit.Replace('\', '/')
if ($tclBit -match '[{}]') { throw 'Unsupported braces in path.' }
$downloadTcl = @"
get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number $CableSerial} result]} {
    puts "PROGRAM_CHAIN_FAIL `$result"
    exit 1
}
puts "PROGRAM_EXPECTED_TARGET jfmql30 part 0 IDCODE 0x9372c093"
if {[catch {program_bit {$tclBit} -part 0} result]} {
    puts "PROGRAM_TCL_FAIL `$result"
    exit 1
}
puts "PROGRAM_TCL_COMPLETED"
if {[catch {read_reg -part 0 -reg STAT -read} result]} {
    puts "STATUS_READ_UNAVAILABLE `$result"
} else {
    puts "STATUS_READ_RESULT `$result"
}
exit
"@
[IO.File]::WriteAllText((Join-Path $programDir 'download.tcl'), $downloadTcl, [Text.Encoding]::ASCII)
Write-Output "Programming reviewed bitstream: $bit"
Invoke-NativeTcl 'download'
$download = Get-Content -LiteralPath (Join-Path $programDir 'download.stdout.log') -Raw
if ($download -notmatch 'PROGRAM_TCL_COMPLETED' -or $download -notmatch 'program_bit elapsed_time' -or
    $download -notmatch 'SVF instructions execute success' -or
    (Get-Item -LiteralPath (Join-Path $programDir 'download.stderr.log')).Length -ne 0) {
    throw 'Native download did not complete cleanly.'
}
$statusMatch = [regex]::Match($download, 'cfg-reg stat:\s*(0x[0-9a-fA-F]+)')
$record = [ordered]@{
    status = 'native_program_command_completed_visual_result_pending'
    timestamp = (Get-Date).ToString('o')
    cable_type = 'usb-jtag-hs1'
    cable_display_name = 'DIGILENT/JTAG-HS1'
    cable_serial = $CableSerial
    target_part = 0
    target_idcode = '0x9372c093'
    bitstream = $bit
    bitstream_sha256 = $review.bitstream_sha256
    configuration = 'volatile FPGA JTAG configuration'
    board_visual_result = 'pending_user_observation'
    stat_register = $(if ($statusMatch.Success) { $statusMatch.Groups[1].Value } else { 'unknown' })
    logs_directory = $programDir
}
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $programDir 'program-result.json') -Encoding UTF8
Write-Output "Native programming command completed. Logs: $programDir"
Get-Content -LiteralPath (Join-Path $programDir 'download.stdout.log')
