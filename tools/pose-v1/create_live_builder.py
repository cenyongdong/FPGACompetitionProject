"""One-time explicit derivation of the audited SDK build workflow, without editing it."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'tools/pose-v1/Build-LivePipeline.ps1';assert not target.exists()
source=(root/'tools/pose-v1/Build-Resident.ps1').read_text(encoding='utf-8')
source=source.replace('# User executes this script. Independent mixed candidate; never runs its binary.','# Agent executes the approved integration build. No devices or model forward.')
source=source.replace('mixed-20261008-resident-r1','mixed-20261008-live-r1').replace('pose_resident_check','pose_live_pipeline_check')
anchor="Invoke-MixedDocker @('exec',$poseContainer,'cmake','-S'"
assert source.count(anchor)==1
vendor=r'''# Copy the already pinned vendor headers/libs into this isolated build.
$poseVendor='D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\单路PLIM+VPU\fpai_demo_package_26040702\fpai_demo_package_26040702\deps\thirdparty'
foreach($poseEntry in $poseManifest.vendor_files.PSObject.Properties){
    if((Get-FileHash -LiteralPath (Join-Path $poseVendor $poseEntry.Name) -Algorithm SHA256).Hash.ToLower() -ne $poseEntry.Value){throw 'Vendor payload changed'}
}
$poseManifest.vendor_files | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $poseOutput 'vendor-files.json') -Encoding utf8
Invoke-MixedDocker @('exec',$poseContainer,'mkdir','-p',($poseRemote+'/vendor/libs'))
Invoke-MixedDocker @('cp',(Join-Path $poseVendor 'include/live'),($poseContainer+':'+$poseRemote+'/vendor/live'))
Invoke-MixedDocker @('cp',(Join-Path $poseVendor 'include/openssl'),($poseContainer+':'+$poseRemote+'/vendor/openssl'))
foreach($poseLib in @('libliveMedia.a','libgroupsock.a','libBasicUsageEnvironment.a','libUsageEnvironment.a','libssl.a','libcrypto.a')){
    Invoke-MixedDocker @('cp',(Join-Path $poseVendor ('a/'+$poseLib)),($poseContainer+':'+$poseRemote+'/vendor/libs/'+$poseLib))
}
'''
source=source.replace(anchor,vendor+'\n'+anchor)
source=source.replace("'--target','pose_live_pipeline_check','--parallel'","'--target','pose_live_pipeline_check','pose_access_unit_selftest','--parallel'")
anchor="$poseHashes = [ordered]@{}";assert source.count(anchor)==1
source=source.replace(anchor,"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_access_unit_selftest'),(Join-Path $poseOutput 'pose_access_unit_selftest'))\n"+anchor)
source=source.replace("stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    au_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_access_unit_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
target.write_bytes(source.encode('utf-8'));print(target)
