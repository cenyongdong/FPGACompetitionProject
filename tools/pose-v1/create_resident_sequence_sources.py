"""Create isolated resident orchestration; frozen computation sources untouched."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def fresh(rel,text):
    p=root/rel
    if p.exists():assert p.read_text(encoding='utf-8')==text;return
    p.write_text(text,encoding='utf-8',newline='\n')
def change(text,old,new):assert text.count(old)==1,old;return text.replace(old,new)
old=(root/'software/pose_v1/src/producer_count_observation.cpp').read_text(encoding='utf-8')
fresh('software/pose_v1/src/resident_producer_count_observation.cpp',change(old,'rows_.size()<824','rows_.size()<856'))
test=(root/'software/pose_v1/src/producer_count_observation_selftest.cpp').read_text(encoding='utf-8').replace('i<103','i<107').replace('size()==824','size()==856').replace('complete(bounded,103)','complete(bounded,107)').replace('maximum_rows\\":824','maximum_rows\\":856')
fresh('software/pose_v1/src/resident_producer_count_selftest.cpp',test)
cm=(root/'tools/pose-v1/model-vpu-CMakeLists.txt').read_text(encoding='utf-8')+'''
add_executable(pose_resident_sequence_check resident_sequence_check.cpp resident_sequence.cpp model_load_lifecycle.cpp model_only_run.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp pipeline_fixture_source.cpp presaved_result_evidence.cpp application_core.cpp application_bridge.cpp host_cpu_adapter.cpp preprocess.cpp host_failure_evidence.cpp failure_source_readback.cpp host_stage_observation.cpp invocation_evidence.cpp resident_producer_count_observation.cpp tensor_identity_observation.cpp)
target_include_directories(pose_resident_sequence_check PRIVATE .)
target_link_libraries(pose_resident_sequence_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_resident_sequence_check PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_resident_sequence_selftest resident_sequence_selftest.cpp resident_sequence.cpp model_load_lifecycle.cpp)
target_include_directories(pose_resident_sequence_selftest PRIVATE .)
target_link_libraries(pose_resident_sequence_selftest PRIVATE Threads::Threads)
target_compile_options(pose_resident_sequence_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
add_executable(pose_resident_producer_selftest resident_producer_count_selftest.cpp resident_producer_count_observation.cpp)
target_include_directories(pose_resident_producer_selftest PRIVATE .)
target_link_libraries(pose_resident_producer_selftest PRIVATE Threads::Threads)
target_compile_options(pose_resident_producer_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
fresh('tools/pose-v1/resident-sequence-CMakeLists.txt',cm)
b=(root/'tools/pose-v1/Build-ModelVpu.ps1').read_text(encoding='utf-8').replace('mixed-20261010-model-vpu-r1','mixed-20261010-resident-sequence-r1')
b=change(b,"'pose_model_load_selftest','--parallel'","'pose_model_load_selftest','pose_resident_sequence_check','pose_resident_sequence_selftest','pose_resident_producer_selftest','--parallel'")
b=change(b,'$poseHashes = [ordered]@{}',"""foreach ($poseNew in @('pose_resident_sequence_check','pose_resident_sequence_selftest','pose_resident_producer_selftest')) {
    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$poseNew),(Join-Path $poseOutput $poseNew))
}
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_resident_sequence_check'))
$poseHashes = [ordered]@{}""")
b=change(b,"stage='compiled_not_executed'; container='FPAI';","""stage='compiled_not_executed'; container='FPAI';
    resident_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_resident_sequence_check') -Algorithm SHA256).Hash.ToLowerInvariant();
    resident_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_resident_sequence_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();
    resident_producer_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_resident_producer_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();""")
fresh('tools/pose-v1/Build-ResidentSequence.ps1',b)
review=(root/'tools/pose-v1/review_model_vpu_build_base.py').read_text(encoding='utf-8').replace('Build-ModelVpu.ps1','Build-ResidentSequence.ps1').replace('len(sections)==5','len(sections)==6')
review=change(review,"'model_vpu_frozen_sources')","'model_vpu_frozen_sources','resident_frozen_sources')")
fresh('tools/pose-v1/review_resident_sequence_build_base.py',review)
print('Isolated sources/configuration created; no build or device operation.')
