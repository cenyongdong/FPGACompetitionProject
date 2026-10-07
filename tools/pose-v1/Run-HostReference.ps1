# User-run Host reference with the previously approved independent DLL bundle.
param(
    [Parameter(Mandatory=$true)][string]$BuildDirectory,
    [Parameter(Mandatory=$true)][string]$Package,
    [Parameter(Mandatory=$true)][string]$Output,
    [string]$RuntimeRoot = 'D:\FPGACompetitionProject\.local\icraft-runtime\cuda-11.8.0'
)
$ErrorActionPreference = 'Stop'
function Native-Quote([string]$Argument) {
    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') { return $Argument }
    $escaped = [regex]::Replace($Argument, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}
$runtime = (Resolve-Path -LiteralPath $RuntimeRoot).Path
$manifestPath = Join-Path $runtime 'runtime-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$icraftBin = 'C:\Icraft\CLI v3.39.0\bin'
if ($manifest.schema_version -ne 1 -or $manifest.icraft_version -ne '3.39.0' -or
    $manifest.cuda_distribution -ne '11.8.0' -or $manifest.icraft_bin -ne $icraftBin) {
    throw 'Unexpected approved dependency manifest; stop.'
}
$prefix = $runtime.TrimEnd('\') + '\'
$bins = @($icraftBin)
$dllCount = 0
foreach ($name in @('libcublas','libcufft')) {
    $components = @($manifest.components | Where-Object {$_.name -eq $name})
    if ($components.Count -ne 1) { throw 'Missing/ambiguous dependency component.' }
    foreach ($dll in $components[0].dlls) {
        $path = [IO.Path]::GetFullPath([string]$dll.path)
        if (-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'DLL outside approved directory.' }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $dll.sha256) { throw 'DLL hash changed.' }
        $dllCount++
    }
    foreach ($bin in $components[0].bin_dirs) {
        $path = (Resolve-Path -LiteralPath $bin).Path
        if (-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Bin outside approved directory.' }
        $bins += $path
    }
}
if ($dllCount -ne 3) { throw 'Expected exactly three approved DLLs.' }
$exe = Join-Path (Resolve-Path -LiteralPath $BuildDirectory).Path 'Release\pose_inference_check.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Expected VS Release binary missing; discuss actual generator/output.' }
$packagePath = (Resolve-Path -LiteralPath $Package).Path
$outputPath = [IO.Path]::GetFullPath($Output)
$logDir = $outputPath + '.launcher'
if ((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $logDir)) { throw 'Output/log directory exists; stop without overwrite.' }
New-Item -ItemType Directory -Path $logDir | Out-Null
$arguments = @('host','--graph',(Join-Path $packagePath 'models\piw24_optimized.json'),
    '--raw',(Join-Path $packagePath 'models\piw24_optimized.raw'),
    '--inputs',(Join-Path $packagePath 'inputs'),'--reference-tokens',(Join-Path $packagePath 'reference'),
    '--output',$outputPath)
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = $exe
$start.Arguments = (($arguments | ForEach-Object {Native-Quote $_}) -join ' ')
$start.WorkingDirectory = $packagePath
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.EnvironmentVariables['PATH'] = ($bins -join ';') + ';' + $env:PATH
$process = New-Object System.Diagnostics.Process
$process.StartInfo = $start
$encoding = New-Object System.Text.UTF8Encoding($false)
try {
    if (-not $process.Start()) { throw 'Host process did not start.' }
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $timedOut = -not $process.WaitForExit(300000)
    if ($timedOut) { $process.Kill(); $process.WaitForExit() }
    [IO.File]::WriteAllText((Join-Path $logDir 'stdout.log'),$stdout.GetAwaiter().GetResult(),$encoding)
    [IO.File]::WriteAllText((Join-Path $logDir 'stderr.log'),$stderr.GetAwaiter().GetResult(),$encoding)
    $record = @{ executable=$exe; binary_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
        arguments=$arguments; child_path_prefix=$bins; runtime_manifest=$manifestPath
        timed_out=$timedOut; exit_code=$process.ExitCode; numerical_acceptance='pending_comparison' }
    [IO.File]::WriteAllText((Join-Path $logDir 'execution.json'),($record | ConvertTo-Json -Depth 5),$encoding)
    if ($timedOut -or $process.ExitCode -ne 0) { throw "Host failed/timed out; retain $logDir and stop." }
    Write-Host "Host reference returned; numerical acceptance pending. Logs: $logDir"
} finally { $process.Dispose() }
