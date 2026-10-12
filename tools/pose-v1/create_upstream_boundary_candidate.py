"""Public producer-boundary observations, isolated from frozen targets."""
import json,shutil,re
import mixed_validation_gate as g
r=g.ROOT
def read(p):return (r/p).read_text(encoding='utf-8')
def fresh(p,s):
    p=r/p;assert not p.exists(),p;p.write_text(s,encoding='utf-8',newline='\n')
cm=read('tools/pose-v1/final-evidence-CMakeLists.txt');start=cm.index('add_executable(pose_final_evidence_check ');end=cm.index('add_executable(pose_final_source_selftest ')
block=cm[start:end].replace('pose_final_evidence_check','pose_upstream_boundary_check').replace('final_evidence_check.cpp','upstream_boundary_check.cpp').replace(' application_core.cpp ',' upstream_application_core.cpp upstream_boundary_sdk.cpp upstream_boundary.cpp ')
extra='''
add_executable(pose_upstream_boundary_selftest upstream_boundary_selftest.cpp upstream_boundary.cpp)
target_include_directories(pose_upstream_boundary_selftest PRIVATE .)
target_link_libraries(pose_upstream_boundary_selftest PRIVATE Threads::Threads)
target_compile_options(pose_upstream_boundary_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
add_executable(pose_upstream_boundary_sdk_selftest upstream_boundary_sdk_selftest.cpp upstream_boundary_sdk.cpp upstream_boundary.cpp)
target_include_directories(pose_upstream_boundary_sdk_selftest PRIVATE .)
target_link_libraries(pose_upstream_boundary_sdk_selftest PRIVATE Icraft::HostBackend Threads::Threads)
target_compile_options(pose_upstream_boundary_sdk_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
fresh('tools/pose-v1/upstream-boundary-CMakeLists.txt',cm+block+extra)
ps=read('tools/pose-v1/Build-FinalEvidence.ps1').replace("'mixed-20261010-final-evidence-r1'","'mixed-20261011-upstream-boundary-r1'",1)
ps=ps.replace("$poseContainer = 'FPAI'","$poseContainer = 'FPAI'\n$poseFrozenRemote = '/tmp/pose-v1-mixed-20261010-final-evidence-r2'",1)
# Compile only three new targets. The36 frozen artifacts are reused verbatim,
# with verified source and prior build provenance, rather than silently rebuilt.
begin=ps.index("    '--target','pose_live_pipeline_check'");finish=ps.index("'--parallel','2')",begin)+len("'--parallel','2')")
ps=ps[:begin]+"    '--target','pose_upstream_boundary_check','pose_upstream_boundary_selftest','pose_upstream_boundary_sdk_selftest','--parallel','2')"+ps[finish:]
lines=[]
for line in ps.splitlines():
    if "'/build/" in line and ('Invoke-MixedDocker' in line or '$poseBinary' in line) and 'cmake' not in line:line=line.replace('$poseRemote','$poseFrozenRemote')
    if "Invoke-MixedDocker @('exec',$poseContainer,'g++'" in line:line='# Frozen native reference is copied verbatim; parent build is never written.'
    lines.append(line)
ps='\n'.join(lines)+'\n'
marker='$poseHashes = [ordered]@{}'
extra_ps="""foreach ($poseUpstream in @('pose_upstream_boundary_check','pose_upstream_boundary_selftest','pose_upstream_boundary_sdk_selftest')) {
    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$poseUpstream),(Join-Path $poseOutput $poseUpstream))
}
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_upstream_boundary_check'))
$posePriorBuild = Join-Path $poseRoot '.local/pose-v1-build/mixed-20261010-final-evidence-r2'
$poseFrozenProof = [ordered]@{}
foreach ($poseFrozen in (Get-ChildItem -LiteralPath $posePriorBuild -File | Where-Object { $_.Name.StartsWith('pose_') })) {
    $poseCurrent = Join-Path $poseOutput $poseFrozen.Name
    if (!(Test-Path -LiteralPath $poseCurrent)) { throw 'Frozen artifact not copied.' }
    $poseDigest = (Get-FileHash -LiteralPath $poseCurrent -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($poseDigest -ne (Get-FileHash -LiteralPath $poseFrozen.FullName -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'Frozen artifact changed.' }
    $poseFrozenProof[$poseFrozen.Name] = $poseDigest
}
[System.IO.File]::WriteAllText((Join-Path $poseOutput 'frozen-build-reuse.json'),(($poseFrozenProof | ConvertTo-Json) + "`n"),[System.Text.UTF8Encoding]::new($false))
"""
assert marker in ps;ps=ps.replace(marker,extra_ps+marker,1)
ps=ps.replace("    stage='compiled_not_executed';","    upstream_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_upstream_boundary_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    upstream_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_upstream_boundary_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    upstream_sdk_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_upstream_boundary_sdk_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    stage='compiled_not_executed';",1)
fresh('tools/pose-v1/Build-UpstreamBoundary.ps1',ps)
base=read('tools/pose-v1/review_final_evidence_r2_build_base.py').replace('Build-FinalEvidence.ps1','Build-UpstreamBoundary.ps1').replace("'final_evidence_r1_frozen_sources')","'final_evidence_r1_frozen_sources','upstream_frozen_sources')").replace('len(sections)==10','len(sections)==11').replace("'Built target pose_system_timing_selftest'","'Built target pose_upstream_boundary_check'")
base=base.replace("    return m,b,n", "    prior=root/'.local/pose-v1-build/mixed-20261010-final-evidence-r2'\n    proof=load(build/'frozen-build-reuse.json');assert len(proof)==36\n    for name,digest in proof.items():assert sha(build/name)==sha(prior/name)==digest\n    return m,b,n",1)
fresh('tools/pose-v1/review_upstream_boundary_build_base.py',base)
stage=read('tools/pose-v1/review_final_evidence_r2_stage.py').replace('review_final_evidence_r2_build_base','review_upstream_boundary_build_base').replace('final_binary_sha256','upstream_binary_sha256').replace('pose_final_evidence_check','pose_upstream_boundary_check').replace('run-final-evidence.sh','run-upstream-boundary.sh')
fresh('tools/pose-v1/review_upstream_boundary_stage.py',stage)
runner=read('tools/pose-v1/run-final-evidence.sh').replace('final_binary_sha256','upstream_binary_sha256').replace('pose_final_evidence_check','pose_upstream_boundary_check')
marker='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
insert='''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_upstream_boundary_selftest" "$run/pose_upstream_boundary_selftest"
    timeout --signal=TERM --kill-after=2s 20s "$work/pose_upstream_boundary_selftest" "$run/upstream-contracts" > "$run/upstream-contracts.stdout.log" 2> "$run/upstream-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/upstream-contracts.exit.txt"
fi
if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_upstream_boundary_sdk_selftest" "$run/pose_upstream_boundary_sdk_selftest"
    timeout --signal=TERM --kill-after=2s 30s "$work/pose_upstream_boundary_sdk_selftest" "$package/graph/piw24_ZG.json" "$run/upstream-sdk-contracts" > "$run/upstream-sdk-contracts.stdout.log" 2> "$run/upstream-sdk-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/upstream-sdk-contracts.exit.txt"
fi
'''
assert marker in runner;runner=runner.replace(marker,insert+marker,1);fresh('tools/pose-v1/run-upstream-boundary.sh',runner)
base=r/'.local/pose-v1-final-evidence/package-20261010-r2';g.verify(base);m=g.load(base/'manifest.json');m['upstream_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()};m['build_files'].pop('tools/pose-v1/final-evidence-CMakeLists.txt')
for name in ['upstream_boundary.hpp','upstream_boundary_sdk.hpp']:
    rel='software/pose_v1/include/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(r/rel))
for name in ['upstream_boundary.cpp','upstream_boundary_sdk.cpp','upstream_boundary_selftest.cpp','upstream_boundary_sdk_selftest.cpp','upstream_application_core.cpp','upstream_boundary_check.cpp']:
    rel='software/pose_v1/src/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(r/rel))
rel='tools/pose-v1/upstream-boundary-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=g.sha(r/rel))
for name in ['create_upstream_boundary_candidate.py','Build-UpstreamBoundary.ps1','review_upstream_boundary_build_base.py','review_upstream_boundary_stage.py','run-upstream-boundary.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(r/rel)
m['build_script']='tools/pose-v1/Build-UpstreamBoundary.ps1';m['upstream_boundary']=dict(points=8,first_complete_frames=4,last_frame=True,owned_frame_bytes=101600,maximum_rows=824,pre_callback_vector_is_outputs=True,inputs_via_retained_public_producer=True,public_wait_ms=10000,hardware_seconds=180,diagnostic_fps=5.05,original_Gather=True,registration_overridden=False,frozen_artifacts_reused=36)
out=r/'.local/pose-v1-upstream-boundary/package-20261011-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
