# User-operated cross compilation only. Does not run binaries or contact Lite.
param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^/[A-Za-z0-9_./+-]+$')][string]$SdkCmakeDir,
    [string]$Docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe',
    [string]$Container = 'FPAI'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$tag = 'inference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,8))
$output = Join-Path $projectRoot ('.local\pose-v1-build\' + $tag)
$remote = '/tmp/pose-v1-' + $tag
New-Item -ItemType Directory -Path $output | Out-Null
$log = Join-Path $output 'build.log'
function Invoke-DockerChecked {
    param([string[]]$CommandArgs)
    & $Docker @CommandArgs 2>&1 | Tee-Object -FilePath $log -Append | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed ($LASTEXITCODE); stop and retain $output" }
}
@{
    state='prepared_user_build'; source_root=$projectRoot; container=$Container
    remote_root=$remote; sdk_cmake_dir=$SdkCmakeDir
    files=@(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'software\pose_v1') -Recurse -File |
        ForEach-Object { @{path=$_.FullName; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()} })
} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $output 'source-manifest.json') -Encoding UTF8
Invoke-DockerChecked -CommandArgs @('exec',$Container,'mkdir','-p',$remote)
Invoke-DockerChecked -CommandArgs @('cp',(Join-Path $projectRoot 'software\pose_v1'),($Container + ':' + $remote + '/source'))
Invoke-DockerChecked -CommandArgs @('cp',(Join-Path $PSScriptRoot 'aarch64-icraft.cmake'),($Container + ':' + $remote + '/toolchain.cmake'))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'test','-f',($SdkCmakeDir + '/icraft-hostbackend-config.cmake'))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'test','-f',($SdkCmakeDir + '/icraft-zg330backend-config.cmake'))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'aarch64-linux-gnu-g++','--version')
Invoke-DockerChecked -CommandArgs @('exec',$Container,'cmake','--version')
Invoke-DockerChecked -CommandArgs @('exec',$Container,'cmake','-S',($remote + '/source'),'-B',($remote + '/build'),
    ('-DCMAKE_TOOLCHAIN_FILE=' + $remote + '/toolchain.cmake'),'-DCMAKE_BUILD_TYPE=Release',
    '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG',
    '-DPOSE_BUILD_ICRAFT_CHECK=ON','-DPOSE_ENABLE_ZG330=ON',('-DCMAKE_PREFIX_PATH=' + $SdkCmakeDir))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'cmake','--build',($remote + '/build'),'--target','pose_inference_check','--parallel','2')
Invoke-DockerChecked -CommandArgs @('cp',($Container + ':' + $remote + '/build/pose_inference_check'),(Join-Path $output 'pose_inference_check.arm64'))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'file',($remote + '/build/pose_inference_check'))
Invoke-DockerChecked -CommandArgs @('exec',$Container,'aarch64-linux-gnu-readelf','-d',($remote + '/build/pose_inference_check'))
Get-FileHash -LiteralPath (Join-Path $output 'pose_inference_check.arm64') -Algorithm SHA256 |
    Format-List | Out-String | Set-Content -LiteralPath (Join-Path $output 'binary-sha256.txt') -Encoding UTF8
Write-Host "Compile completed. No software tests or board operations executed. Evidence: $output"
