param(
    [string]$BoardHost = '192.168.126.49',
    [string]$BoardUser = 'root',
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\board-audit.json')
)
$ErrorActionPreference = 'Stop'
$payload = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'board_probe.py')))
$remote = "python3 -c 'import base64;exec(base64.b64decode(" + [char]34 + $payload + [char]34 + "))'"
$transport = & 'C:\Windows\System32\OpenSSH\ssh.exe' -T `
    -o StrictHostKeyChecking=yes -o ConnectTimeout=8 `
    -o ServerAliveInterval=5 -o ServerAliveCountMax=2 `
    -o NumberOfPasswordPrompts=1 -o PreferredAuthentications=password `
    -o PubkeyAuthentication=no "$BoardUser@$BoardHost" $remote
if ($LASTEXITCODE -ne 0) { throw 'Read-only board audit failed; no device access is approved by this result.' }
$joined = $transport -join "`n"
$match = [regex]::Match($joined, 'POSE_AUDIT_BEGIN\s+([A-Za-z0-9+/=\s]+)\s+POSE_AUDIT_END')
if (-not $match.Success) { throw 'Audit evidence transport incomplete.' }
$json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($match.Groups[1].Value -replace '\s', '')))
$audit = $json | ConvertFrom-Json
if ($audit.boot_partition_error) { throw $audit.boot_partition_error }
$envelope = [ordered]@{
    checked_at = (Get-Date).ToString('o')
    board_host = $BoardHost
    probe_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'board_probe.py') -Algorithm SHA256).Hash.ToLower()
    audit = $audit
}
$directory = Split-Path -Parent $EvidencePath
[IO.Directory]::CreateDirectory($directory) | Out-Null
[IO.File]::WriteAllText($EvidencePath, ($envelope | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
Write-Output "Read-only audit saved: $EvidencePath"
Write-Output "FAT boot files: $($audit.boot_partition.files.Count); FPGA state: $($audit.fpga_state)"
