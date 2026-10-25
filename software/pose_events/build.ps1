param([string]$BuildDir = "$PSScriptRoot/../../.local/pose-events-direct")
$ErrorActionPreference = 'Stop'
$compiler = (Get-Command g++.exe -ErrorAction Stop).Source
$taskBuild = [IO.Path]::GetFullPath($BuildDir)
New-Item -ItemType Directory -Force -Path $taskBuild | Out-Null
$flags = @('-std=c++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-ffp-contract=off',"-I$PSScriptRoot")
$object = Join-Path $taskBuild 'reference.o'
& $compiler @flags -c "$PSScriptRoot/reference.cpp" -o $object
if ($LASTEXITCODE -ne 0) { throw "Reference compile failed: $LASTEXITCODE" }
foreach ($target in @(@('offline.cpp','pose_events_offline.exe'),@('test/reference_tests.cpp','pose_events_tests.exe'))) {
    & $compiler @flags (Join-Path $PSScriptRoot $target[0]) $object -o (Join-Path $taskBuild $target[1])
    if ($LASTEXITCODE -ne 0) { throw "Native build failed: $($target[1]), $LASTEXITCODE" }
}
Write-Output "Built standalone C++17 PS prototype with $compiler in $taskBuild"
