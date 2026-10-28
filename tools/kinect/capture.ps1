param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [ValidateRange(1,600)][int]$Seconds = 60,
    [string]$BoardHost,
    [int]$BoardPort = 39383,
    [switch]$DepthDiagnostic
)
$ErrorActionPreference = 'Stop'
$kinectProject = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$kinectBin = Join-Path $kinectProject '.local/kinect-check-20261028-r1/bin/ExportBodies.exe'
if (!(Test-Path -LiteralPath $kinectBin)) { & (Join-Path $PSScriptRoot 'build.ps1') }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a new capture directory.' }
$kinectOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $kinectOutput | Out-Null
$kinectTap = $null
try {
    if ($BoardHost) {
        $kinectNode = (Get-Command node -ErrorAction Stop).Source
        $kinectTapArgs = @(('"'+(Join-Path $PSScriptRoot 'receive_full.mjs')+'"'),$BoardHost,('"'+(Join-Path $kinectOutput 'csi')+'"'),[string]$Seconds,[string]$BoardPort)
        $kinectTap = Start-Process -FilePath $kinectNode -ArgumentList $kinectTapArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $kinectOutput 'csi.log') -RedirectStandardError (Join-Path $kinectOutput 'csi-error.log')
    }
    $kinectArgs = @((Join-Path $kinectOutput 'kinect'),[string]$Seconds)
    if ($DepthDiagnostic) { $kinectArgs += '--depth-diagnostic' }
    & $kinectBin @kinectArgs 2>&1 | Tee-Object -FilePath (Join-Path $kinectOutput 'kinect.log')
    $kinectExit = $LASTEXITCODE
    if ($kinectTap) { $kinectTap.WaitForExit() }
    @{schema='KINECT-PAIRED-SESSION1';kinect_exit=$kinectExit;passive_csi_subscriber=[bool]$BoardHost;CSI_or_board_started=$false;training_started=$false;finished_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $kinectOutput 'session.json') -Encoding UTF8
    if ($kinectExit -ne 0) { throw "Kinect capture did not export a tracked body; exit=$kinectExit" }
} finally {
    # The passive subscriber owns its finite timer and closes itself. Do not kill unrelated processes.
    if ($kinectTap -and !$kinectTap.HasExited) { $kinectTap.WaitForExit() }
}
