"""Isolated owned-picture entry; retain every prior source and binary."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def read(rel):return (root/rel).read_text(encoding='utf-8')
def put(rel,text):p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def change(text,old,new):assert text.count(old)==1,old;return text.replace(old,new)
# Expose the exact historical marker and fingerprint as SDK-free functions.
old=read('software/pose_v1/src/resident_owner_check.cpp');begin=old.index('void mark(');end=old.index('\nint run(',begin)
helpers=old[begin:end].replace('void mark(','void markEncodedId(')
put('software/pose_v1/src/picture_marker.cpp','#include "picture_source.hpp"\n#include <algorithm>\n#include <sstream>\n#include <iomanip>\nnamespace pose::picture {\n'+helpers+'\n}\n')
seq=read('software/pose_v1/src/resident_sequence.cpp');put('software/pose_v1/src/picture_sequence.cpp',change(seq,'{"load-103",4,103,200000000}','{"load-103",4,103,500000000}'))
seqtest=read('software/pose_v1/src/resident_sequence_selftest.cpp');put('software/pose_v1/src/picture_sequence_selftest.cpp',change(seqtest,'p.period==(phase?200000000:500000000)','p.period==500000000'))
s=read('software/pose_v1/src/resident_sequence_check.cpp').replace('#include "scratch_vpu_load.hpp"','#include "picture_vpu.hpp"\n#include "skeleton_render.hpp"').replace('pose::scratch::VpuLoad','pose::picture::Vpu')
s=change(s,'    const auto entry=now();','''    fs::create_directory(out/"pictures");
    std::array<float,100> emptyScores{};std::array<float,4200> emptyPoses{};
    auto noInput=pose_v1::render::draw(emptyScores,emptyPoses,0,pose_v1::render::Status::NoInput);
    pose::video::OwnedFrame warm;warm.nv12=pose_v1::render::yuv420sp(noInput.rgb,1280,720,false);warm.generatedNs=now();warm.inferenceResult=false;
    proof::persistBytes(out/"pictures/warmup.nv12",warm.nv12.data(),warm.nv12.size());
    auto pictures=file(out/"pictures/index.jsonl");
    const auto entry=now();''')
s=change(s,'video=std::make_unique<pose::picture::Vpu>(out/"vpu");','video=std::make_unique<pose::picture::Vpu>(out/"vpu",std::move(warm));')
s=change(s,'                    proof::saveThenVerifyResult(fixture,r.result,actual,global,out,calls);stamps.back().verified=now();load.check();','''                    proof::saveThenVerifyResult(fixture,r.result,actual,global,out,calls);stamps.back().verified=now();load.check();
                    const auto drawBegin=now();auto rgb=pose_v1::render::draw(r.result.scores,r.result.poses,r.result.frame_id);
                    need(rgb.top_index==r.result.best_index,"Picture highest candidate differs");
                    for(const auto& point:rgb.projected){need(point[1]<590,"Joint intersects encoded marker");}
                    const auto drawEnd=now();pose::video::OwnedFrame frame;frame.nv12=pose_v1::render::yuv420sp(rgb.rgb,1280,720,false);
                    frame.sourceFrame=r.result.frame_id;frame.invocation=global;frame.generatedNs=now();
                    const auto name="result"+std::to_string(global)+".nv12";
                    proof::persistBytes(out/"pictures"/name,frame.nv12.data(),frame.nv12.size());
                    pictures<<"{\\"invocation\\":"<<global<<",\\"frame_id\\":"<<frame.sourceFrame<<",\\"case\\":"<<std::quoted(c.name)<<",\\"file\\":"<<std::quoted(name)<<",\\"bytes\\":"<<frame.nv12.size()<<",\\"best_index\\":"<<rgb.top_index<<",\\"draw_begin_ns\\":"<<drawBegin<<",\\"draw_end_ns\\":"<<drawEnd<<",\\"convert_end_ns\\":"<<frame.generatedNs<<",\\"publish_begin_ns\\":"<<now()<<"}\\n";pictures.flush();need(bool(pictures),"Picture metadata write failed");
                    video->publish(std::move(frame));load.check();''')
s=change(s,'life.close();stages.close();need(bool(life)&&bool(stages),','life.close();stages.close();pictures.close();need(bool(life)&&bool(stages)&&bool(pictures),')
s=s.replace('resident-three-103','picture-three-103').replace('one Engine and one synthetic VPU lifecycle','one Engine and one owned-picture VPU lifecycle')
put('software/pose_v1/src/picture_check.cpp',s)
cm=read('tools/pose-v1/resident-sequence-CMakeLists.txt')+'''
add_executable(pose_picture_check picture_check.cpp picture_sequence.cpp picture_source.cpp picture_marker.cpp picture_vpu.cpp skeleton_render.cpp model_load_lifecycle.cpp model_only_run.cpp timed_resident_encoder.cpp pipeline_fixture_source.cpp presaved_result_evidence.cpp application_core.cpp application_bridge.cpp host_cpu_adapter.cpp preprocess.cpp host_failure_evidence.cpp failure_source_readback.cpp host_stage_observation.cpp invocation_evidence.cpp resident_producer_count_observation.cpp tensor_identity_observation.cpp)
target_include_directories(pose_picture_check PRIVATE .)
target_link_libraries(pose_picture_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_picture_check PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_picture_source_selftest picture_source_selftest.cpp picture_source.cpp picture_marker.cpp)
target_include_directories(pose_picture_source_selftest PRIVATE .)
target_link_libraries(pose_picture_source_selftest PRIVATE Threads::Threads)
target_compile_options(pose_picture_source_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
add_executable(pose_picture_sequence_selftest picture_sequence_selftest.cpp picture_sequence.cpp model_load_lifecycle.cpp)
target_include_directories(pose_picture_sequence_selftest PRIVATE .)
target_link_libraries(pose_picture_sequence_selftest PRIVATE Threads::Threads)
target_compile_options(pose_picture_sequence_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
put('tools/pose-v1/picture-CMakeLists.txt',cm)
b=read('tools/pose-v1/Build-ResidentSequence.ps1').replace('mixed-20261010-resident-sequence-r1','mixed-20261010-picture-r1')
b=change(b,"'pose_resident_producer_selftest','--parallel'","'pose_resident_producer_selftest','pose_picture_check','pose_picture_source_selftest','pose_picture_sequence_selftest','--parallel'")
b=change(b,'$poseHashes = [ordered]@{}',"""foreach ($posePicture in @('pose_picture_check','pose_picture_source_selftest','pose_picture_sequence_selftest')) {
    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$posePicture),(Join-Path $poseOutput $posePicture))
}
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_picture_check'))
$poseHashes = [ordered]@{}""")
b=change(b,"stage='compiled_not_executed'; container='FPAI';","""stage='compiled_not_executed'; container='FPAI';
    picture_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_picture_check') -Algorithm SHA256).Hash.ToLowerInvariant();
    picture_source_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_picture_source_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();
    picture_sequence_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_picture_sequence_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();""")
put('tools/pose-v1/Build-Picture.ps1',b)
review=read('tools/pose-v1/review_resident_sequence_build_base.py').replace('Build-ResidentSequence.ps1','Build-Picture.ps1').replace('len(sections)==6','len(sections)==7')
review=change(review,"'resident_frozen_sources')","'resident_frozen_sources','picture_frozen_sources')")
put('tools/pose-v1/review_picture_build_base.py',review)
print('Owned picture sources and build configuration created; no device accessed.')
