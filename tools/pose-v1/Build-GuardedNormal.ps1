param([string]$BuildTag='guarded-normal-20261008-r1')
$ErrorActionPreference='Stop'
if($BuildTag -notmatch '^guarded-normal-[a-zA-Z0-9_-]+$'){throw 'Unsafe build tag'}
$poseRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$poseOutput=Join-Path $poseRoot ('.local/pose-v1-build/'+$BuildTag)
if(Test-Path -LiteralPath $poseOutput){throw 'Preserve existing build'}
$poseVendor='D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\单路PLIM+VPU\fpai_demo_package_26040702\fpai_demo_package_26040702\deps\thirdparty'
$poseDocker='C:\Program Files\Docker\Docker\resources\bin\docker.exe'
$poseRemote='/tmp/pose-'+$BuildTag
New-Item -ItemType Directory -Path $poseOutput | Out-Null
$poseFiles=@('include/h264_access_unit.hpp','include/access_unit_channel.hpp','include/online_rtsp.hpp','include/guarded_rtsp.hpp',
 'src/h264_access_unit.cpp','src/access_unit_channel.cpp','src/guarded_rtsp.cpp','src/access_unit_selftest.cpp','src/rtsp_guarded_normal_check.cpp')
$poseSources=@{}
foreach($poseFile in $poseFiles){
 $poseOriginal=Join-Path $poseRoot ('software/pose_v1/'+$poseFile)
 Copy-Item -LiteralPath $poseOriginal -Destination $poseOutput
 $poseSources['software/pose_v1/'+$poseFile]=(Get-FileHash -LiteralPath $poseOriginal -Algorithm SHA256).Hash.ToLower()
}
$poseIdentity=@{}
@(Get-ChildItem -LiteralPath (Join-Path $poseVendor 'include/live') -File -Recurse; Get-ChildItem -LiteralPath (Join-Path $poseVendor 'include/openssl') -File -Recurse) | ForEach-Object {
 $poseIdentity[$_.FullName.Substring($poseVendor.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
}
$poseLibs=@('libliveMedia.a','libgroupsock.a','libBasicUsageEnvironment.a','libUsageEnvironment.a','libssl.a','libcrypto.a')
foreach($poseLib in $poseLibs){$poseIdentity['a/'+$poseLib]=(Get-FileHash -LiteralPath (Join-Path $poseVendor ('a/'+$poseLib)) -Algorithm SHA256).Hash.ToLower()}
$poseBaseline=Get-Content -Raw -LiteralPath (Join-Path $poseRoot '.local/pose-v1-build/rtsp-replay-20261007-r2/vendor-files.json') | ConvertFrom-Json
if(@($poseBaseline.PSObject.Properties).Count -ne $poseIdentity.Count){throw 'Vendor file count changed'}
foreach($poseEntry in $poseBaseline.PSObject.Properties){if($poseIdentity[$poseEntry.Name] -ne $poseEntry.Value){throw 'Vendor bytes changed'}}
$poseIdentity | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $poseOutput 'vendor-files.json') -Encoding utf8
function Invoke-OwnedDocker([string[]]$CommandArgs){
 $posePreference=$ErrorActionPreference
 try{$ErrorActionPreference='Continue'; & $poseDocker @CommandArgs 2>&1 | ForEach-Object {$_.ToString()} | Tee-Object -FilePath (Join-Path $poseOutput 'build.log') -Append | Out-Host; $poseExit=$LASTEXITCODE}
 finally{$ErrorActionPreference=$posePreference}
 if($poseExit -ne 0){throw "Owned RTSP build/gate stopped ($poseExit); preserve logs"}
}
Invoke-OwnedDocker @('exec','FPAI','test','!','-e',$poseRemote)
Invoke-OwnedDocker @('exec','FPAI','mkdir','-p',($poseRemote+'/libs'))
foreach($poseFile in $poseFiles){$poseName=Split-Path -Leaf $poseFile;Invoke-OwnedDocker @('cp',(Join-Path $poseOutput $poseName),('FPAI:'+$poseRemote+'/'+$poseName))}
Invoke-OwnedDocker @('exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',('-I'+$poseRemote),($poseRemote+'/h264_access_unit.cpp'),($poseRemote+'/access_unit_channel.cpp'),($poseRemote+'/access_unit_selftest.cpp'),'-pthread','-o',($poseRemote+'/host_selftest'))
Invoke-OwnedDocker @('exec','FPAI',($poseRemote+'/host_selftest'))
Invoke-OwnedDocker @('cp',(Join-Path $poseVendor 'include/live'),('FPAI:'+$poseRemote+'/live'))
Invoke-OwnedDocker @('cp',(Join-Path $poseVendor 'include/openssl'),('FPAI:'+$poseRemote+'/openssl'))
foreach($poseLib in $poseLibs){Invoke-OwnedDocker @('cp',(Join-Path $poseVendor ('a/'+$poseLib)),('FPAI:'+$poseRemote+'/libs/'+$poseLib))}
Invoke-OwnedDocker @('exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',('-I'+$poseRemote),($poseRemote+'/h264_access_unit.cpp'),($poseRemote+'/access_unit_channel.cpp'),($poseRemote+'/access_unit_selftest.cpp'),'-pthread','-o',($poseRemote+'/pose_access_unit_selftest'))
Invoke-OwnedDocker @('exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',('-I'+$poseRemote),('-I'+$poseRemote+'/live/liveMedia/include'),('-I'+$poseRemote+'/live/BasicUsageEnvironment/include'),('-I'+$poseRemote+'/live/UsageEnvironment/include'),('-I'+$poseRemote+'/live/groupsock/include'),($poseRemote+'/h264_access_unit.cpp'),($poseRemote+'/access_unit_channel.cpp'),($poseRemote+'/guarded_rtsp.cpp'),($poseRemote+'/rtsp_guarded_normal_check.cpp'),('-L'+$poseRemote+'/libs'),'-Wl,--start-group','-lliveMedia','-lgroupsock','-lBasicUsageEnvironment','-lUsageEnvironment','-lssl','-lcrypto','-Wl,--end-group','-ldl','-pthread','-o',($poseRemote+'/pose_rtsp_guarded_normal_check'))
Invoke-OwnedDocker @('exec','FPAI','aarch64-linux-gnu-readelf','-d',($poseRemote+'/pose_rtsp_guarded_normal_check'))
$posePrograms=@{}
foreach($poseProgram in @('pose_access_unit_selftest','pose_rtsp_guarded_normal_check')){
 Invoke-OwnedDocker @('cp',('FPAI:'+$poseRemote+'/'+$poseProgram),(Join-Path $poseOutput $poseProgram))
 $posePrograms[$poseProgram]=(Get-FileHash -LiteralPath (Join-Path $poseOutput $poseProgram) -Algorithm SHA256).Hash.ToLower()
}
@{sources=$poseSources;programs=$posePrograms;vendor_files=$poseIdentity.Count;builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLower();scope='native_host_gate_and_ARM_build_no_devices';native_selftest_passed=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $poseOutput 'build-result.json') -Encoding utf8
