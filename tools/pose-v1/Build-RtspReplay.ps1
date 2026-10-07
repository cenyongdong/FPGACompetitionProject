param([string]$BuildTag='rtsp-replay-20261007-r2')
$ErrorActionPreference='Stop'
if($BuildTag -notmatch '^rtsp-replay-[a-zA-Z0-9_-]+$'){throw 'Unsafe build tag'}
$poseRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$poseOutput=Join-Path $poseRoot ('.local/pose-v1-build/'+$BuildTag)
if(Test-Path -LiteralPath $poseOutput){throw 'Preserve existing build'}
$poseVendor='D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\单路PLIM+VPU\fpai_demo_package_26040702\fpai_demo_package_26040702\deps\thirdparty'
$poseDocker='C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseRemote='/tmp/pose-'+$BuildTag
New-Item -ItemType Directory -Path $poseOutput | Out-Null
Copy-Item -LiteralPath (Join-Path $poseRoot 'software/pose_v1/src/rtsp_replay_check.cpp') -Destination $poseOutput
$poseIdentity=@{}
@(Get-ChildItem -LiteralPath (Join-Path $poseVendor 'include/live') -File -Recurse; Get-ChildItem -LiteralPath (Join-Path $poseVendor 'include/openssl') -File -Recurse) | ForEach-Object {
  $poseIdentity[$_.FullName.Substring($poseVendor.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
}
$poseLibs=@('libliveMedia.a','libgroupsock.a','libBasicUsageEnvironment.a','libUsageEnvironment.a','libssl.a','libcrypto.a')
foreach($poseLib in $poseLibs){$poseIdentity['a/'+$poseLib]=(Get-FileHash -LiteralPath (Join-Path $poseVendor ('a/'+$poseLib)) -Algorithm SHA256).Hash.ToLower()}
$poseIdentity | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $poseOutput 'vendor-files.json') -Encoding utf8
function Invoke-RtspDocker([string[]]$CommandArgs) {
  $posePreference=$ErrorActionPreference
  try {$ErrorActionPreference='Continue'; & $poseDocker @CommandArgs 2>&1 | ForEach-Object {$_.ToString()} | Tee-Object -FilePath (Join-Path $poseOutput 'build.log') -Append | Out-Host; $poseExit=$LASTEXITCODE}
  finally {$ErrorActionPreference=$posePreference}
  if($poseExit -ne 0){throw "Build stopped ($poseExit); preserve logs"}
}
Invoke-RtspDocker @('exec','FPAI','test','!','-e',$poseRemote)
Invoke-RtspDocker @('exec','FPAI','mkdir','-p',($poseRemote+'/libs'))
Invoke-RtspDocker @('cp',(Join-Path $poseVendor 'include/live'),('FPAI:'+$poseRemote+'/live'))
Invoke-RtspDocker @('cp',(Join-Path $poseVendor 'include/openssl'),('FPAI:'+$poseRemote+'/openssl'))
Invoke-RtspDocker @('cp',(Join-Path $poseOutput 'rtsp_replay_check.cpp'),('FPAI:'+$poseRemote+'/rtsp_replay_check.cpp'))
foreach($poseLib in $poseLibs){Invoke-RtspDocker @('cp',(Join-Path $poseVendor ('a/'+$poseLib)),('FPAI:'+$poseRemote+'/libs/'+$poseLib))}
Invoke-RtspDocker @('exec','FPAI','aarch64-linux-gnu-g++','--version')
Invoke-RtspDocker @('exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',('-I'+$poseRemote),
  ('-I'+$poseRemote+'/live/liveMedia/include'),('-I'+$poseRemote+'/live/BasicUsageEnvironment/include'),
  ('-I'+$poseRemote+'/live/UsageEnvironment/include'),('-I'+$poseRemote+'/live/groupsock/include'),
  ($poseRemote+'/rtsp_replay_check.cpp'),('-L'+$poseRemote+'/libs'),'-Wl,--start-group','-lliveMedia','-lgroupsock','-lBasicUsageEnvironment','-lUsageEnvironment','-lssl','-lcrypto','-Wl,--end-group','-ldl','-lpthread','-o',($poseRemote+'/pose_rtsp_replay_check'))
Invoke-RtspDocker @('exec','FPAI','aarch64-linux-gnu-readelf','-d',($poseRemote+'/pose_rtsp_replay_check'))
Invoke-RtspDocker @('cp',('FPAI:'+$poseRemote+'/pose_rtsp_replay_check'),(Join-Path $poseOutput 'pose_rtsp_replay_check'))
Write-Output "Build complete; no streaming/devices executed: $poseOutput"
