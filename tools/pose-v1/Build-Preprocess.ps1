param([string]$Container = 'FPAI')
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$source = Join-Path $project 'software\pose_v1'
$artifacts = Join-Path $project '.local\pose-v1-build'
[IO.Directory]::CreateDirectory($artifacts) | Out-Null
$docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
function Invoke-PoseDocker([string[]]$DockerArgs) {
    & $docker @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker build/check failed: $($DockerArgs[0])" }
}
$remoteSource = '/tmp/pose-v1-source-' + [guid]::NewGuid().ToString('N')
Invoke-PoseDocker @('cp', $source, "${Container}:$remoteSource")
$common = @('-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic',
    "-I$remoteSource/include",
    "$remoteSource/src/preprocess.cpp",
    "$remoteSource/src/preprocess_check.cpp")
Invoke-PoseDocker (@('exec',$Container,'g++') + $common + @('-o','/tmp/pose-v1-preprocess-host'))
Invoke-PoseDocker @('exec',$Container,'/tmp/pose-v1-preprocess-host','--self-test')
Invoke-PoseDocker (@('exec',$Container,'aarch64-linux-gnu-g++') + $common + @('-o','/tmp/pose-v1-preprocess-arm64'))
Invoke-PoseDocker @('cp',"${Container}:/tmp/pose-v1-preprocess-arm64",(Join-Path $artifacts 'pose_preprocess_check.arm64'))
Get-FileHash -LiteralPath (Join-Path $artifacts 'pose_preprocess_check.arm64') -Algorithm SHA256
