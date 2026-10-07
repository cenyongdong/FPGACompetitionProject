param([string]$BuildTag='vpu-sequence-20261007-r1')
$ErrorActionPreference='Stop'
if($BuildTag -notmatch '^vpu-sequence-[a-zA-Z0-9_-]+$'){throw 'Unsafe build tag'}
$poseRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$poseOutput=Join-Path $poseRoot ('.local/pose-v1-build/'+$BuildTag)
if(Test-Path -LiteralPath $poseOutput){throw 'Preserve existing build; use new revision'}
$poseDocker='C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseRemote='/tmp/pose-'+$BuildTag
New-Item -ItemType Directory -Path $poseOutput | Out-Null
foreach($poseFile in @('src/vpu_encoder.cpp','src/vpu_sequence_check.cpp','include/vpu_encoder.hpp')) {
  Copy-Item -LiteralPath (Join-Path $poseRoot ('software/pose_v1/'+$poseFile)) -Destination $poseOutput
}
function Invoke-SequenceDocker([string[]]$CommandArgs) {
  $posePreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & $poseDocker @CommandArgs 2>&1 | ForEach-Object {$_.ToString()} | Tee-Object -FilePath (Join-Path $poseOutput 'build.log') -Append | Out-Host
    $poseExit=$LASTEXITCODE
  } finally {$ErrorActionPreference=$posePreference}
  if($poseExit -ne 0){throw "Build stopped ($poseExit); preserve logs"}
}
Invoke-SequenceDocker @('exec','FPAI','test','!','-e',$poseRemote)
Invoke-SequenceDocker @('exec','FPAI','mkdir',$poseRemote)
foreach($poseFile in @('vpu_encoder.cpp','vpu_sequence_check.cpp','vpu_encoder.hpp')) {
  Invoke-SequenceDocker @('cp',(Join-Path $poseOutput $poseFile),('FPAI:'+$poseRemote+'/'+$poseFile))
}
Invoke-SequenceDocker @('exec','FPAI','aarch64-linux-gnu-g++','--version')
Invoke-SequenceDocker @('exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',($poseRemote+'/vpu_encoder.cpp'),($poseRemote+'/vpu_sequence_check.cpp'),'-o',($poseRemote+'/pose_vpu_sequence_check'))
Invoke-SequenceDocker @('exec','FPAI','aarch64-linux-gnu-readelf','-d',($poseRemote+'/pose_vpu_sequence_check'))
Invoke-SequenceDocker @('exec','FPAI','sha256sum','/usr/aarch64-linux-gnu/include/linux/videodev2.h','/usr/aarch64-linux-gnu/include/linux/v4l2-controls.h')
Invoke-SequenceDocker @('cp',('FPAI:'+$poseRemote+'/pose_vpu_sequence_check'),(Join-Path $poseOutput 'pose_vpu_sequence_check'))
Write-Output "Build complete; no VPU/HDMI/NPU executed: $poseOutput"
