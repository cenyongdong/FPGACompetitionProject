"""One binary, two controlled load modes, all model/encoder bytes frozen."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=read('software/pose_v1/src/model_only_check.cpp')
s=change(s,'#include "model_only_run.hpp"','#include "model_only_run.hpp"\n#include "model_load_lifecycle.hpp"\n#include "scratch_vpu_load.hpp"')
s=change(s,'    need(argc==6,"three|load-103 PACKAGE FRESH-RESULTS --finite-check --allow-device-init");\n    const std::string mode=argv[1];const fs::path package=argv[2],out=argv[3];const bool expanded=mode=="load-103";\n    need((expanded||mode=="three")&&std::string(argv[4])=="--finite-check"&&std::string(argv[5])=="--allow-device-init"&&!fs::exists(out),"Model-only mode/permission/preserve contract differs");', '''    need(argc==7||argc==8,"model|model-vpu three|load-103 PACKAGE FRESH-RESULTS --finite-check --allow-device-init [--allow-vpu-stream]");
    const std::string loadMode=argv[1],mode=argv[2];const bool withVpu=loadMode=="model-vpu";
    const fs::path package=argv[3],out=argv[4];const bool expanded=mode=="load-103";
    need((loadMode=="model"||withVpu)&&(expanded||mode=="three")&&std::string(argv[5])=="--finite-check"&&std::string(argv[6])=="--allow-device-init"&&!fs::exists(out)&&(withVpu?argc==8&&std::string(argv[7])=="--allow-vpu-stream":argc==7),"Paired model/VPU permission differs");''')
s=change(s,'    fs::create_directory(out/"engine");','''    std::unique_ptr<pose::scratch::VpuLoad>video;
    pose::load_lifecycle::Control load(withVpu,{
        [&]{video=std::make_unique<pose::scratch::VpuLoad>(out/"vpu");},
        [&]{video->waitReady();lifecycle<<"{\\"event\\":\\"VPU_actual_capture\\",\\"time_ns\\":"<<now()<<"}\\n";lifecycle.flush();},
        [&]{if(video){video->check();}},
        [&]{if(video){video->join();}},
        [&](bool abort){if(video){video->requestStop(abort);}}
    });
    fs::create_directory(out/"engine");''')
s=change(s,'    try{\n        app::Config cfg;','    try{\n        load.start();\n        app::Config cfg;')
s=change(s,'        for(size_t i=0;i<count;++i){','        for(size_t i=0;i<count;++i){\n            load.check();')
s=change(s,'                stamps.back().verified=now();','                stamps.back().verified=now();load.check();')
s=change(s,'    const bool computeFailed=bool(failure);','''    load.finish(failure);
    need(load.joined(),"Load worker not joined before Engine release");
    lifecycle<<"{\\"event\\":\\"load_joined\\",\\"time_ns\\":"<<now()<<",\\"enabled\\":"<<(withVpu?"true":"false")<<"}\\n";
    const bool computeFailed=bool(failure);''')
s=change(s,'    auto summary=file(out/"summary.json");','    video.reset();\n    auto summary=file(out/"summary.json");')
s=change(s,'<<",\\"sdk_profiling\\":false,\\"VPU\\":false,\\"display\\":false,\\"network\\":false,\\"HDMI\\":false,\\"NPU_forward\\":true}\\n"','<<",\\"sdk_profiling\\":false,\\"VPU\\":"<<(withVpu?"true":"false")<<",\\"load_joined\\":true,\\"display\\":false,\\"network\\":false,\\"HDMI\\":false,\\"NPU_forward\\":true}\\n"')
s=change(s,'<<"; no VPU/display/network.\\n"','<<"; synthetic VPU="<<withVpu<<"; no display/network.\\n"')
put('software/pose_v1/src/model_vpu_check_r1.cpp',s)
cm=read('tools/pose-v1/model-only-CMakeLists.txt')+'''
add_executable(pose_model_vpu_check model_vpu_check.cpp model_load_lifecycle.cpp model_only_run.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp pipeline_fixture_source.cpp presaved_result_evidence.cpp application_core.cpp application_bridge.cpp host_cpu_adapter.cpp preprocess.cpp host_failure_evidence.cpp failure_source_readback.cpp host_stage_observation.cpp invocation_evidence.cpp producer_count_observation.cpp tensor_identity_observation.cpp)
target_include_directories(pose_model_vpu_check PRIVATE .)
target_link_libraries(pose_model_vpu_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_model_vpu_check PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_model_load_selftest model_load_selftest.cpp model_load_lifecycle.cpp)
target_include_directories(pose_model_load_selftest PRIVATE .)
target_link_libraries(pose_model_load_selftest PRIVATE Threads::Threads)
target_compile_options(pose_model_load_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
put('tools/pose-v1/model-vpu-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-ModelOnly.ps1').replace('mixed-20261010-model-only-r1','mixed-20261010-model-vpu-r1')
builder=change(builder,"'pose_model_only_selftest','--parallel'","'pose_model_only_selftest','pose_model_vpu_check','pose_model_load_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_model_vpu_check'),(Join-Path $poseOutput 'pose_model_vpu_check'))\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_model_load_selftest'),(Join-Path $poseOutput 'pose_model_load_selftest'))\nInvoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_model_vpu_check'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    model_vpu_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_model_vpu_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    load_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_model_load_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-ModelVpu.ps1',builder)
review=read('tools/pose-v1/review_model_only_build_base.py').replace('Build-ModelOnly.ps1','Build-ModelVpu.ps1');review=change(review,"'model_only_frozen_sources')","'model_only_frozen_sources','model_vpu_frozen_sources')");review=change(review,'assert len(sections)==4','assert len(sections)==5')
put('tools/pose-v1/review_model_vpu_build_base.py',review)
base=root/'.local/pose-v1-model-only/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json');m['model_vpu_frozen_sources']={rel:item['sha256'] for rel,item in m['build_files'].items()}
old='tools/pose-v1/model-only-CMakeLists.txt';new='tools/pose-v1/model-vpu-CMakeLists.txt';m['build_files'].pop(old);m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(root/new))
for rel,dest in {'software/pose_v1/src/model_vpu_check_r1.cpp':'model_vpu_check.cpp','software/pose_v1/include/model_load_lifecycle.hpp':'model_load_lifecycle.hpp','software/pose_v1/src/model_load_lifecycle.cpp':'model_load_lifecycle.cpp','software/pose_v1/src/model_load_selftest.cpp':'model_load_selftest.cpp'}.items():m['build_files'][rel]=dict(destination=dest,sha256=g.sha(root/rel))
for name in ['prepare_model_vpu_r1.py','Build-ModelVpu.ps1','review_model_vpu_build_base.py','run-model-vpu.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ModelVpu.ps1';m['model_vpu']=dict(stages=['contracts','model-three','vpu-three','model-103','vpu-103'],same_binary=True,synthetic_NoInput=True,encoder_limit=1000,first_capture_seconds=5,engine_init_seconds=60,total_seconds=180,network=False,display=False,normal_source_reads_added=0)
out=root/'.local/pose-v1-model-vpu/package-20261010-r1';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
