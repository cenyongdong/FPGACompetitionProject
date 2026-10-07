# User executes this script. Independent mixed candidate; never runs its binary.
param([Parameter(Mandatory=$true)][string]$Package,
      [string]$BuildTag = 'mixed-20261007-application-r1')
$ErrorActionPreference = 'Stop'
if ($BuildTag -notmatch '^mixed-[a-zA-Z0-9_-]+$') { throw 'Unsafe build tag.' }
$poseRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$posePackage = (Resolve-Path -LiteralPath $Package).Path
$poseManifestPath = Join-Path $posePackage 'manifest.json'
$poseManifest = Get-Content -LiteralPath $poseManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$poseDocker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseContainer = 'FPAI'
$poseRemote = '/tmp/pose-v1-' + $BuildTag
$poseOutput = Join-Path $poseRoot ('.local\pose-v1-build\' + $BuildTag)
if (Test-Path -LiteralPath $poseOutput) { throw 'Build directory exists; preserve evidence and stop.' }
if (-not (Test-Path -LiteralPath $poseDocker -PathType Leaf)) { throw 'Confirmed Docker executable missing.' }
foreach ($entry in $poseManifest.build_files.PSObject.Properties) {
    $source = Join-Path $poseRoot $entry.Name
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256) {
        throw "Source differs from prepared fixtures: $($entry.Name)"
    }
}
New-Item -ItemType Directory -Path $poseOutput | Out-Null
$poseSource = Join-Path $poseOutput 'source'
New-Item -ItemType Directory -Path $poseSource | Out-Null
foreach ($entry in $poseManifest.build_files.PSObject.Properties) {
    Copy-Item -LiteralPath (Join-Path $poseRoot $entry.Name) -Destination (Join-Path $poseSource $entry.Value.destination)
}
Copy-Item -LiteralPath $poseManifestPath -Destination (Join-Path $poseSource 'fixture-manifest.json')
$poseLog = Join-Path $poseOutput 'build.log'
function Invoke-MixedDocker {
    param([string[]]$CommandArgs)
    # Windows PowerShell wraps native stderr as ErrorRecord. Log every line,
    # then use the actual native exit code; do not abort on the first stderr.
    $poseSavedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $poseDocker @CommandArgs 2>&1 | ForEach-Object { $_.ToString() } |
            Tee-Object -FilePath $poseLog -Append | Out-Host
        $poseNativeExit = $LASTEXITCODE
    } finally { $ErrorActionPreference = $poseSavedPreference }
    if ($poseNativeExit -ne 0) { throw "Mixed candidate build stopped ($poseNativeExit); preserve $poseOutput" }
}
Invoke-MixedDocker @('exec',$poseContainer,'test','!','-e',$poseRemote)
Invoke-MixedDocker @('exec',$poseContainer,'mkdir',$poseRemote)
Invoke-MixedDocker @('cp',$poseSource,($poseContainer + ':' + $poseRemote + '/source'))
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-g++','--version')
Invoke-MixedDocker @('exec',$poseContainer,'cmake','--version')
# SDK audit runs in Windows; FPAI needs no Python interpreter.
# Retain exact exported bytes, then normalize CRLF only for header identities.
$poseSnapshot = Join-Path $poseOutput 'sdk-snapshot'
New-Item -ItemType Directory -Path $poseSnapshot | Out-Null
$poseVersions = [ordered]@{}
foreach ($posePackageName in @('icraft:arm64','customop:arm64')) {
    $poseVersionLines = @(& $poseDocker exec $poseContainer dpkg-query -W '-f=${Version}' $posePackageName 2>&1)
    $poseVersionExit = $LASTEXITCODE
    $poseVersionLines | Tee-Object -FilePath $poseLog -Append | Out-Host
    if ($poseVersionExit -ne 0) { throw "SDK package query failed: $posePackageName" }
    $poseVersion = ($poseVersionLines -join "`n").Trim()
    if ($poseVersion -ne '3.39.0') { throw "SDK version differs: $posePackageName $poseVersion" }
    $poseVersions[$posePackageName] = $poseVersion
}
$poseHeaderHashes = [ordered]@{}
$poseUtf8 = [System.Text.UTF8Encoding]::new($false,$true)
foreach ($poseHeader in $poseManifest.sdk_headers_normalized_sha256.PSObject.Properties) {
    $poseHeaderFile = Join-Path $poseSnapshot $poseHeader.Name
    New-Item -ItemType Directory -Path (Split-Path -Parent $poseHeaderFile) -Force | Out-Null
    Invoke-MixedDocker @('cp','-L',($poseContainer + ':/usr/include/' + $poseHeader.Name),$poseHeaderFile)
    $poseHeaderText = $poseUtf8.GetString([System.IO.File]::ReadAllBytes($poseHeaderFile))
    $poseHeaderBytes = $poseUtf8.GetBytes($poseHeaderText.Replace("`r`n","`n"))
    $poseHasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        $poseHeaderHash = [System.BitConverter]::ToString($poseHasher.ComputeHash($poseHeaderBytes)).Replace('-','').ToLowerInvariant()
    } finally { $poseHasher.Dispose() }
    if ($poseHeaderHash -ne $poseHeader.Value) { throw "SDK header baseline differs: $($poseHeader.Name)" }
    $poseHeaderHashes[$poseHeader.Name] = $poseHeaderHash
}
$poseHostSnapshot = Join-Path $poseSnapshot 'libicraft_hostbackend.so'
Invoke-MixedDocker @('cp','-L',($poseContainer + ':/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so'),$poseHostSnapshot)
$poseHostHash = (Get-FileHash -LiteralPath $poseHostSnapshot -Algorithm SHA256).Hash.ToLowerInvariant()
if ($poseHostHash -ne $poseManifest.host_library_sha256) { throw 'ARM Host library baseline differs.' }
$poseZgSnapshot = Join-Path $poseSnapshot 'libicraft_zg330backend.so'
Invoke-MixedDocker @('cp','-L',($poseContainer + ':/usr/lib/aarch64-linux-gnu/libicraft_zg330backend.so'),$poseZgSnapshot)
$poseZgHash = (Get-FileHash -LiteralPath $poseZgSnapshot -Algorithm SHA256).Hash.ToLowerInvariant()
if ($poseZgHash -ne $poseManifest.zg_library_sha256) { throw 'ARM ZG library baseline differs.' }
$poseAudit = [ordered]@{
    versions=$poseVersions; headers_normalized_sha256=$poseHeaderHashes; host_sha256=$poseHostHash; zg_sha256=$poseZgHash;
    method='docker_copy_and_windows_sha256'; container_python_required=$false
}
[System.IO.File]::WriteAllText((Join-Path $poseOutput 'sdk-audit.json'),
    (($poseAudit | ConvertTo-Json -Depth 8) + "`n"),[System.Text.UTF8Encoding]::new($false))
Write-Host 'ARM SDK versions, copied headers and Host/ZG libraries matched; no candidate executed.'
Invoke-MixedDocker @('exec',$poseContainer,'cmake','-S',($poseRemote+'/source'),'-B',($poseRemote+'/build'),
    ('-DCMAKE_TOOLCHAIN_FILE='+$poseRemote+'/source/toolchain.cmake'),'-DCMAKE_BUILD_TYPE=Release',
    '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_PREFIX_PATH=/usr/cmake')
Invoke-MixedDocker @('exec',$poseContainer,'cmake','--build',($poseRemote+'/build'),
    '--target','pose_application_render_check','pose_skeleton_render_check','pose_video_capability_probe','--parallel','2')
Invoke-MixedDocker @('exec',$poseContainer,'file',($poseRemote+'/build/pose_application_render_check'))
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_application_render_check'))
$poseBinary = Join-Path $poseOutput 'pose_application_render_check.arm64'
Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_application_render_check'),$poseBinary)
$poseTransport = Join-Path $poseOutput 'pose_skeleton_render_check.arm64'
Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_skeleton_render_check'),$poseTransport)
$poseVideoProbe = Join-Path $poseOutput 'pose_video_capability_probe.arm64'
Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_video_capability_probe'),$poseVideoProbe)
$poseHashes = [ordered]@{}
foreach ($entry in $poseManifest.build_files.PSObject.Properties) {
    $poseHashes[$entry.Name] = (Get-FileHash -LiteralPath (Join-Path $poseSource $entry.Value.destination) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$poseResult = [ordered]@{
    stage='compiled_not_executed'; container='FPAI';
    video_probe_sha256=(Get-FileHash -LiteralPath $poseVideoProbe -Algorithm SHA256).Hash.ToLowerInvariant();
    renderer_binary_sha256=(Get-FileHash -LiteralPath $poseTransport -Algorithm SHA256).Hash.ToLowerInvariant(); sdk_config='/usr/cmake';
    build_script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();
    source_sha256=$poseHashes;
    package_manifest_sha256=(Get-FileHash -LiteralPath $poseManifestPath -Algorithm SHA256).Hash.ToLowerInvariant();
    binary_sha256=(Get-FileHash -LiteralPath $poseBinary -Algorithm SHA256).Hash.ToLowerInvariant();
    device_accessed=$false; mixed_verified=$false
}
[System.IO.File]::WriteAllText((Join-Path $poseOutput 'build-result.json'),
    (($poseResult | ConvertTo-Json -Depth 8) + "`n"),[System.Text.UTF8Encoding]::new($false))
Write-Host "Compilation completed, no tests/model/device operations executed. Review: $poseOutput"
