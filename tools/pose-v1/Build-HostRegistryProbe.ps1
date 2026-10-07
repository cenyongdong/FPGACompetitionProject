# Approved special-problem diagnostic build. No model or board execution.
$ErrorActionPreference = 'Stop'
$poseRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$poseDocker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseContainer = 'FPAI'
$poseRemote = '/tmp/pose-v1-host-registry-20261005'
$poseOutput = Join-Path $poseRoot '.local\pose-v1-build\host-registry-20261005'
if (Test-Path -LiteralPath $poseOutput) { throw 'Probe build directory exists; preserve and stop.' }
New-Item -ItemType Directory -Path $poseOutput | Out-Null
$poseSource = Join-Path $poseOutput 'source'
New-Item -ItemType Directory -Path $poseSource | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'host-registry-probe.candidate.cpp') -Destination $poseSource
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'host-registry-probe-CMakeLists.candidate.txt') -Destination (Join-Path $poseSource 'CMakeLists.txt')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'aarch64-icraft.cmake') -Destination (Join-Path $poseOutput 'toolchain.cmake')
Get-ChildItem -LiteralPath $poseSource -File | ForEach-Object {
    [ordered]@{ name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $poseOutput 'source-manifest.json') -Encoding utf8
$poseLog = Join-Path $poseOutput 'build.log'
function Invoke-ProbeDocker {
    param([string[]]$CommandArgs)
    & $poseDocker @CommandArgs 2>&1 | Tee-Object -FilePath $poseLog -Append | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Diagnostic build failed ($LASTEXITCODE); stop and preserve $poseOutput" }
}
Invoke-ProbeDocker @('exec',$poseContainer,'test','!','-e',$poseRemote)
Invoke-ProbeDocker @('exec',$poseContainer,'mkdir',$poseRemote)
Invoke-ProbeDocker @('cp',$poseSource,($poseContainer + ':' + $poseRemote + '/source'))
Invoke-ProbeDocker @('cp',(Join-Path $poseOutput 'toolchain.cmake'),($poseContainer + ':' + $poseRemote + '/toolchain.cmake'))
Invoke-ProbeDocker @('exec',$poseContainer,'aarch64-linux-gnu-g++','--version')
Invoke-ProbeDocker @('exec',$poseContainer,'cmake','--version')
Invoke-ProbeDocker @('exec',$poseContainer,'dpkg-query','-W','icraft:arm64','customop:arm64')
Invoke-ProbeDocker @('exec',$poseContainer,'cmake','-S',($poseRemote + '/source'),'-B',($poseRemote + '/build'),
    ('-DCMAKE_TOOLCHAIN_FILE=' + $poseRemote + '/toolchain.cmake'),'-DCMAKE_BUILD_TYPE=Release',
    '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_PREFIX_PATH=/usr/cmake')
Invoke-ProbeDocker @('exec',$poseContainer,'cmake','--build',($poseRemote + '/build'),'--target','host_registry_probe','--parallel','2')
Invoke-ProbeDocker @('exec',$poseContainer,'file',($poseRemote + '/build/host_registry_probe'))
Invoke-ProbeDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote + '/build/host_registry_probe'))
Invoke-ProbeDocker @('cp',($poseContainer + ':' + $poseRemote + '/build/host_registry_probe'),(Join-Path $poseOutput 'host_registry_probe.arm64'))
Get-FileHash -LiteralPath (Join-Path $poseOutput 'host_registry_probe.arm64') -Algorithm SHA256 | Format-List | Out-String |
    Set-Content -LiteralPath (Join-Path $poseOutput 'binary-sha256.txt') -Encoding utf8
Write-Host "Diagnostic compile completed; no probe or model has run. Artifacts: $poseOutput"
