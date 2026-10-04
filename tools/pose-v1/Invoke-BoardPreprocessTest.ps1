param(
    [Parameter(Mandatory)][string]$RemoteArchive,
    [Parameter(Mandatory)][string]$ArchiveSha256,
    [string]$BoardHost = '192.168.126.49',
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\board-preprocess.json')
)
$ErrorActionPreference = 'Stop'
if ($RemoteArchive -notmatch '^/tmp/pose-v1-[a-z0-9-]+\.tar\.gz$' -or $ArchiveSha256 -notmatch '^[a-f0-9]{64}$') {
    throw 'Only a verified pose-v1 temporary archive is allowed.'
}
$payload = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'board_preprocess_test.py')))
$remote = "python3 -c 'import sys,base64;sys.argv=[" + [char]34 + 'probe' + [char]34 + ',' + [char]34 + $RemoteArchive + [char]34 + ',' + [char]34 + $ArchiveSha256 + [char]34 + '];exec(base64.b64decode(' + [char]34 + $payload + [char]34 + "))'"
$transport = & 'C:\Windows\System32\OpenSSH\ssh.exe' -T -o StrictHostKeyChecking=yes `
    -o ConnectTimeout=8 -o ServerAliveInterval=5 -o ServerAliveCountMax=2 `
    -o NumberOfPasswordPrompts=1 -o PreferredAuthentications=password -o PubkeyAuthentication=no "root@$BoardHost" $remote
if ($LASTEXITCODE -ne 0) { throw 'Board preprocessing test failed.' }
$match = [regex]::Match(($transport -join "`n"),'POSE_TEST_BEGIN\s+([A-Za-z0-9+/=\s]+)\s+POSE_TEST_END')
if (-not $match.Success) { throw 'Test evidence transport incomplete.' }
$json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($match.Groups[1].Value -replace '\s','')))
$report = $json | ConvertFrom-Json
$report | Add-Member -NotePropertyName 'checked_at' -NotePropertyValue (Get-Date).ToString('o')
$report | Add-Member -NotePropertyName 'tester_sha256' -NotePropertyValue (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'board_preprocess_test.py') -Algorithm SHA256).Hash.ToLower()
[IO.Directory]::CreateDirectory((Split-Path -Parent $EvidencePath)) | Out-Null
[IO.File]::WriteAllText($EvidencePath, ($report | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Write-Output "Board-only math results saved: $EvidencePath"
Write-Output "Cases: $($report.results.Count); self-test: $($report.self_test)"
