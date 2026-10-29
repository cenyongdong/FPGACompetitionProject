param(
	[string]$Board = "192.168.50.49",
	[string]$NodePath = "",
	[string]$LocalAddress = "",
	[switch]$Check
)

$ErrorActionPreference = "Stop"

# Deployment-root launcher. An explicit runtime path takes precedence.
$candidates = @()
if ($NodePath) {
	$candidates += $NodePath
} else {
	$candidates += Join-Path $PSScriptRoot "pc/runtime/node.exe"
	$command = Get-Command node.exe -CommandType Application -ErrorAction SilentlyContinue
	if ($command) {
		$candidates += $command.Source
	}
	if ($env:ProgramFiles) {
		$candidates += Join-Path $env:ProgramFiles "nodejs/node.exe"
	}
	if ($env:LOCALAPPDATA) {
		$candidates += Join-Path $env:LOCALAPPDATA "Programs/nodejs/node.exe"
	}
	if ($env:USERPROFILE) {
		$candidates += Join-Path $env:USERPROFILE ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
	}
}

# Validate the executable itself; the caller's PATH may differ from Codex's.
$nodeExecutable = $null
$nodeVersion = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
	if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
		continue
	}
	try {
		$version = (& $candidate --version 2>&1 | Out-String).Trim()
		if ($LASTEXITCODE -eq 0 -and $version -match '^v(\d+)\.' -and [int]$Matches[1] -ge 20) {
			$nodeExecutable = (Resolve-Path -LiteralPath $candidate).Path
			$nodeVersion = $version
			break
		}
	} catch {
		# A stale runtime location must not hide another usable installation.
	}
}

if (-not $nodeExecutable) {
	throw "Node.js 20 or newer was not found. Supply its executable with -NodePath 'C:\path\to\node.exe'."
}
if ($Check) {
	[pscustomobject]@{ ready = $true; node = $nodeExecutable; version = $nodeVersion } | ConvertTo-Json -Compress
	exit 0
}

$entry = Join-Path $PSScriptRoot "pc/software/pose180_pipeline/host/resident.mjs"
if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) {
	throw "PC entry point is missing. Run this launcher from the extracted deployment package."
}
Write-Host "Using Node.js $nodeVersion ($nodeExecutable)"
$arguments = @($entry, "--board", $Board, "--mode", "view", "--http-port", "39380")
if ($LocalAddress) {
	$arguments += @("--local-address", $LocalAddress)
}
Write-Host "Connecting to board $Board (local address: $(if ($LocalAddress) { $LocalAddress } else { 'automatic' }))"
& $nodeExecutable @arguments
exit $LASTEXITCODE
