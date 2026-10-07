# User executes this script. Independent CPU candidate; never runs its binary.
param([Parameter(Mandatory=$true)][string]$Package,
      [string]$BuildTag = 'cpu-adapter-20261005')
$ErrorActionPreference = 'Stop'
if ($BuildTag -notmatch '^cpu-adapter-[a-zA-Z0-9_-]+$') { throw 'Unsafe build tag.' }
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
function Invoke-CpuDocker {
    param([string[]]$CommandArgs)
    & $poseDocker @CommandArgs 2>&1 | Tee-Object -FilePath $poseLog -Append | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "CPU candidate build stopped ($LASTEXITCODE); preserve $poseOutput" }
}
Invoke-CpuDocker @('exec',$poseContainer,'test','!','-e',$poseRemote)
Invoke-CpuDocker @('exec',$poseContainer,'mkdir',$poseRemote)
Invoke-CpuDocker @('cp',$poseSource,($poseContainer + ':' + $poseRemote + '/source'))
Invoke-CpuDocker @('exec',$poseContainer,'aarch64-linux-gnu-g++','--version')
Invoke-CpuDocker @('exec',$poseContainer,'cmake','--version')
$poseAuditCode = @'
import pathlib,json,hashlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);m=json.loads((root/'source/fixture-manifest.json').read_text())
versions={p:subprocess.check_output(['dpkg-query','-W','-f=${Version}',p],text=True) for p in ['icraft:arm64','customop:arm64']}
assert all(v=='3.39.0' for v in versions.values()),versions
headers={rel:hashlib.sha256((pathlib.Path('/usr/include')/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for rel in m['sdk_headers_normalized_sha256']}
assert headers==m['sdk_headers_normalized_sha256'],'SDK headers differ; stop, do not repair automatically'
host=hashlib.sha256(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so').read_bytes()).hexdigest()
assert host==m['host_library_sha256'],'Host library baseline differs'
(root/'sdk-audit.json').write_text(json.dumps({'versions':versions,'headers_normalized_sha256':headers,'host_sha256':host},indent=2)+'\n')
print('ARM SDK 3.39.0 and normalized headers matched; no candidate executed.')
'@
Invoke-CpuDocker @('exec',$poseContainer,'python3','-c',$poseAuditCode,$poseRemote)
Invoke-CpuDocker @('exec',$poseContainer,'cmake','-S',($poseRemote+'/source'),'-B',($poseRemote+'/build'),
    ('-DCMAKE_TOOLCHAIN_FILE='+$poseRemote+'/source/toolchain.cmake'),'-DCMAKE_BUILD_TYPE=Release',
    '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_PREFIX_PATH=/usr/cmake')
Invoke-CpuDocker @('exec',$poseContainer,'cmake','--build',($poseRemote+'/build'),
    '--target','pose_cpu_adapter_check','--parallel','2')
Invoke-CpuDocker @('exec',$poseContainer,'file',($poseRemote+'/build/pose_cpu_adapter_check'))
Invoke-CpuDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_cpu_adapter_check'))
Invoke-CpuDocker @('cp',($poseContainer+':'+$poseRemote+'/sdk-audit.json'),(Join-Path $poseOutput 'sdk-audit.json'))
$poseBinary = Join-Path $poseOutput 'pose_cpu_adapter_check.arm64'
Invoke-CpuDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_cpu_adapter_check'),$poseBinary)
$poseHashes = [ordered]@{}
foreach ($entry in $poseManifest.build_files.PSObject.Properties) {
    $poseHashes[$entry.Name] = (Get-FileHash -LiteralPath (Join-Path $poseSource $entry.Value.destination) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$poseResult = [ordered]@{
    stage='compiled_not_executed'; container='FPAI'; sdk_config='/usr/cmake';
    source_sha256=$poseHashes;
    package_manifest_sha256=(Get-FileHash -LiteralPath $poseManifestPath -Algorithm SHA256).Hash.ToLowerInvariant();
    binary_sha256=(Get-FileHash -LiteralPath $poseBinary -Algorithm SHA256).Hash.ToLowerInvariant();
    device_accessed=$false; mixed_verified=$false
}
[System.IO.File]::WriteAllText((Join-Path $poseOutput 'build-result.json'),
    (($poseResult | ConvertTo-Json -Depth 8) + "`n"),[System.Text.UTF8Encoding]::new($false))
Write-Host "Compilation completed, no tests/model/device operations executed. Review: $poseOutput"
