<#
.SYNOPSIS
Runs Icraft 3.39.0 with the project's approved, isolated NVIDIA libraries.
.EXAMPLE
& .\tools\Invoke-Icraft.ps1 -IcraftArgs @('run', '--help')
.EXAMPLE
& .\tools\Invoke-Icraft.ps1 -WorkingDirectory 'D:\model_project' -IcraftArgs @('parse', '.\configs\model.toml')
.NOTES
Only the child process PATH changes. Model/device operations still require their
own task authorization. See REFERENCES.md section I5 for validation limits.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$IcraftArgs = @('--help'),
    [string]$WorkingDirectory = (Get-Location).Path,
    [string]$RuntimeRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '.local\icraft-runtime\cuda-11.8.0')
)

$ErrorActionPreference = 'Stop'

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Argument)
    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') {
        return $Argument
    }
    # Windows CRT quoting: double backslashes before quotes and a closing quote.
    $escaped = [regex]::Replace($Argument, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}

function Get-RuntimeSha256 {
    param([string]$LiteralPath)
    # Use the framework API so module autoloading is not a launcher prerequisite.
    $stream = [IO.File]::OpenRead($LiteralPath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

$runtimePath = (Resolve-Path -LiteralPath $RuntimeRoot).ProviderPath
$manifestPath = Join-Path $runtimePath 'runtime-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema_version -ne 1 -or $manifest.icraft_version -ne '3.39.0' -or $manifest.cuda_distribution -ne '11.8.0') {
    throw 'Unexpected runtime manifest; inspect before changing the approved versions.'
}
$icraftBin = 'C:\Icraft\CLI v3.39.0\bin'
if ($manifest.icraft_bin -ne $icraftBin) { throw 'The runtime manifest does not reference the pinned Icraft installation.' }
$icraftExe = Join-Path $icraftBin 'icraft.exe'
if (-not (Test-Path -LiteralPath $icraftExe -PathType Leaf)) { throw "Icraft executable is missing: $icraftExe" }
$runDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).ProviderPath
if (-not (Test-Path -LiteralPath $runDirectory -PathType Container)) { throw 'WorkingDirectory must be an existing directory.' }

$runtimePrefix = $runtimePath.TrimEnd('\') + '\'
$libraryBins = @()
$verifiedDlls = @()
foreach ($componentName in @('libcublas', 'libcufft')) {
    $components = @($manifest.components | Where-Object { $_.name -eq $componentName })
    if ($components.Count -ne 1) { throw "Expected one component: $componentName" }
    foreach ($dll in $components[0].dlls) {
        $dllPath = [IO.Path]::GetFullPath([string]$dll.path)
        if (-not $dllPath.StartsWith($runtimePrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'A runtime DLL path escapes the approved dependency directory.'
        }
        if ((Get-RuntimeSha256 -LiteralPath $dllPath) -ne $dll.sha256) {
            throw "Runtime DLL checksum differs from the verified package: $dllPath"
        }
        $verifiedDlls += $dllPath
    }
    foreach ($bin in $components[0].bin_dirs) {
        $binPath = (Resolve-Path -LiteralPath $bin).ProviderPath
        if (-not $binPath.StartsWith($runtimePrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'A library search path escapes the approved dependency directory.'
        }
        $libraryBins += $binPath
    }
}
if ($verifiedDlls.Count -ne 3) { throw 'Expected the three approved NVIDIA DLLs.' }
$pathPrefix = @($icraftBin) + $libraryBins

$logDirectory = Join-Path $runtimePath 'logs'
[IO.Directory]::CreateDirectory($logDirectory) | Out-Null
$logStem = 'icraft-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$stdoutPath = Join-Path $logDirectory ($logStem + '.stdout.log')
$stderrPath = Join-Path $logDirectory ($logStem + '.stderr.log')
$recordPath = Join-Path $logDirectory ($logStem + '.json')
$utf8 = New-Object System.Text.UTF8Encoding($false)

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $icraftExe
$startInfo.Arguments = (($IcraftArgs | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
$startInfo.WorkingDirectory = $runDirectory
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.StandardOutputEncoding = $utf8
$startInfo.StandardErrorEncoding = $utf8
$startInfo.EnvironmentVariables['PATH'] = ($pathPrefix -join ';') + ';' + $env:PATH
$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
$startedUtc = [DateTime]::UtcNow.ToString('o')
try {
    if (-not $process.Start()) { throw 'Failed to start Icraft.' }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdoutText = $stdoutTask.GetAwaiter().GetResult()
    $stderrText = $stderrTask.GetAwaiter().GetResult()
    $toolExitCode = $process.ExitCode
    [IO.File]::WriteAllText($stdoutPath, $stdoutText, $utf8)
    [IO.File]::WriteAllText($stderrPath, $stderrText, $utf8)
    $record = [ordered]@{
        started_utc = $startedUtc
        completed_utc = [DateTime]::UtcNow.ToString('o')
        executable = $icraftExe
        arguments = @($IcraftArgs)
        working_directory = $runDirectory
        runtime_manifest = $manifestPath
        child_path_prefix = $pathPrefix
        verified_dlls = $verifiedDlls
        exit_code = $toolExitCode
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
    }
    [IO.File]::WriteAllText($recordPath, ($record | ConvertTo-Json -Depth 6) + [Environment]::NewLine, $utf8)
    # Keep stdout/stderr reserved for the actual tool output; metadata is in logs.
    [Console]::Out.Write($stdoutText)
    [Console]::Error.Write($stderrText)
} finally {
    $process.Dispose()
}
exit $toolExitCode
