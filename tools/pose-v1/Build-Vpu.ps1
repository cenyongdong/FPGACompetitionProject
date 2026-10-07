param([string]$BuildTag='vpu-20261007-r1')
$ErrorActionPreference='Stop'
if($BuildTag -notmatch '^vpu-[a-zA-Z0-9_-]+$'){throw 'Unsafe build tag'}
$poseRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$poseOutput=Join-Path $poseRoot ('.local/pose-v1-build/'+$BuildTag)
if(Test-Path -LiteralPath $poseOutput){throw 'Preserve existing build; use new revision'}
$poseDocker='C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseRemote='/tmp/pose-'+$BuildTag
New-Item -ItemType Directory -Path $poseOutput | Out-Null
Copy-Item -LiteralPath (Join-Path $poseRoot 'software/pose_v1/src/vpu_encode_check.cpp') -Destination $poseOutput
function Invoke-VpuDocker([string[]]$CommandArgs) {
  $posePreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & $poseDocker @CommandArgs 2>&1 | ForEach-Object {$_.ToString()} | Tee-Object -FilePath (Join-Path $poseOutput 'build.log') -Append | Out-Host
    $poseExit=$LASTEXITCODE
  } finally {$ErrorActionPreference=$posePreference}
  if($poseExit -ne 0){throw "Build stopped ($poseExit); preserve logs"}
}
Invoke-VpuDocker @('exec','FPAI','test','!','-e',$poseRemote)
Invoke-VpuDocker @('exec','FPAI','mkdir',$poseRemote)
Invoke-VpuDocker @('cp',(Join-Path $poseOutput 'vpu_encode_check.cpp'),('FPAI:'+$poseRemote+'/vpu_encode_check.cpp'))
Invoke-VpuDocker @('exec','FPAI','aarch64-linux-gnu-g++','--version')
Invoke-VpuDocker @('exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',($poseRemote+'/vpu_encode_check.cpp'),'-o',($poseRemote+'/pose_vpu_encode_check'))
Invoke-VpuDocker @('exec','FPAI','aarch64-linux-gnu-readelf','-d',($poseRemote+'/pose_vpu_encode_check'))
Invoke-VpuDocker @('exec','FPAI','sha256sum','/usr/aarch64-linux-gnu/include/linux/videodev2.h','/usr/aarch64-linux-gnu/include/linux/v4l2-controls.h')
Invoke-VpuDocker @('cp',('FPAI:'+$poseRemote+'/pose_vpu_encode_check'),(Join-Path $poseOutput 'pose_vpu_encode_check'))
Write-Output "Build complete; no VPU/HDMI/NPU operation executed: $poseOutput"
