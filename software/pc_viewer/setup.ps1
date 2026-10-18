$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskWork = Join-Path $taskRoot '.local/pc-pose-replay-20261018-r1'
Push-Location $taskRoot
try {
    & node "$PSScriptRoot/tools/fetch-deps.mjs"
    if ($LASTEXITCODE -ne 0) { throw 'Dependency download failed' }
    $taskPackage = Get-Content -Raw "$PSScriptRoot/package.json" | ConvertFrom-Json
    foreach ($taskName in @('three', 'ws')) {
        $taskVersion = $taskPackage.dependencies.$taskName
        $taskDestination = Join-Path $PSScriptRoot "node_modules/$taskName"
        New-Item -ItemType Directory -Force -Path $taskDestination | Out-Null
        & tar -xzf "$taskWork/dependencies/$taskName-$taskVersion.tgz" -C $taskDestination --strip-components 1
        if ($LASTEXITCODE -ne 0) { throw "Dependency extraction failed: $taskName" }
    }
    & node "$PSScriptRoot/tools/prepare.mjs"
    if ($LASTEXITCODE -ne 0) { throw 'Real-result preparation failed' }
    & g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -ffp-contract=off "$taskRoot/software/pose_output/pose_frame.cpp" "$taskRoot/software/pose_output/tcp_sender.cpp" "$taskRoot/software/pose_output/replay.cpp" -o "$taskWork/pose_replay.exe" -static -lws2_32
    if ($LASTEXITCODE -ne 0) { throw 'C++ sender compilation failed' }
} finally { Pop-Location }
