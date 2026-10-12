"""Pin the audited public allocator and isolate higher-position SDK sources."""
import json,shutil,subprocess,hashlib
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/plddr-position-20261010-r1';build=root/'.local/pose-v1-build/plddr-manager-20261010-r1'
def put(rel,text):
    p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
r=e/'manager-return/run-manager';g.verify(r);assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
manager=g.load(r/'results/manager.json');bounds=g.load(r/'results/bounds.json');assert manager['manager_type']=='icraft::xrt::DefaultMemManagerNode' and manager['chunks']==[] and manager['Tensor_malloc_calls']==0
assert bounds==dict(start=4096,capacity=4294963200,end_exclusive=4294967296,initial_chunks=0,large_allocation_executed=False)
assert g.sha(e/'manager-return.tar')=='f90aebee931b23d8e0c4a4736d325df98b3a13f415dd3baaeccaa779790ec8a0'
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
p=subprocess.run([docker,'exec','FPAI','aarch64-linux-gnu-objdump','-d','-C','--start-address=0x36c30','--stop-address=0x36ef0','/usr/lib/aarch64-linux-gnu/libicraft_xrt.so'],capture_output=True);assert p.returncode==0;(build/'MemChunk-constructor.asm').write_bytes(p.stdout)
for p in build.glob('*.asm'):shutil.copyfile(p,e/p.name)
shutil.copyfile(build/'sdk/icraft-xrt/core/device.h',e/'ARM-device.h.txt')
audit=dict(status='public_allocator_audit_passed',stage='manager',bounds=bounds,manager_sha256=g.sha(r/'results/manager.json'),archive_sha256=g.sha(e/'manager-return.tar'),build_result_sha256=g.sha(build/'build-result.json'),disassembly_sha256={p.name:g.sha(p) for p in e.glob('*.asm')},header_sha256=g.sha(e/'ARM-device.h.txt'),Tensor_allocations=0,NPU_forward=False)
(e/'manager.acceptance.json').write_text(json.dumps(audit,indent=2)+'\n')
s=(root/'software/pose_v1/src/typed_scratch_sdk.cpp').read_text(encoding='utf-8')
s=replace(s,'#include "typed_scratch_sdk.hpp"','#include "typed_scratch_sdk.hpp"\n#include "plddr_position_contract.hpp"')
s=replace(s,'struct SdkScratch::Impl {','''namespace {
namespace pc=pose::plddr_position;
pc::Pool snapshot(const xrt::MemRegion&region,const std::filesystem::path&path,size_t expectedCount){
    auto manager=region.memManager();need(std::string(manager->typeKey())=="icraft::xrt::DefaultMemManagerNode","Public manager changed");
    const auto&info=manager.getMemRegionInfo();need(info.count("start")&&info.count("byte_size"),"Public pool information absent");
    const auto*bytes=info.at("byte_size").as<xir::IntImmNode>();need(bytes&&bytes->value>0&&info.at("start").as<xrt::MemPtrNode>(),"Public pool field types differ");
    auto start=xir::Downcast<xrt::MemPtr>(info.at("start"));need(start.ptype()==xrt::PtrType::ADDR,"Public pool pointer is not ADDR");
    pc::Pool pool{start.addr(),uint64_t(bytes->value)};const auto chunks=manager.getAllMemChunk();std::ofstream f(path);
    f<<"{\\"start\\":"<<pool.start<<",\\"bytes\\":"<<pool.bytes<<",\\"manager_type\\":\\"icraft::xrt::DefaultMemManagerNode\\",\\"chunks\\":[";
    for(size_t i=0;i<chunks.size();++i){const auto&c=chunks[i];if(i){f<<',';}need(c->region.same_as(region)&&c->begin.ptype()==xrt::PtrType::ADDR,"Public chunk ownership changed");
        f<<"{\\"address\\":"<<c->begin.addr()<<",\\"bytes\\":"<<c->byte_size<<",\\"identity\\":"<<reinterpret_cast<uintptr_t>(c.operator->())<<",\\"region_owned\\":true}";
    }f<<"]}\\n";f.close();need(bool(f),"Public manager snapshot save failed");need(chunks.size()==expectedCount,"Unexpected public chunks; stop allocation");return pool;
}
pc::Block block(const xrt::Tensor&t,const xrt::MemRegion&r,uint64_t bytes){
    need(t.hasData()&&t.memRegion().same_as(r)&&t.data().ptype()==xrt::PtrType::ADDR&&t.chunk()->begin.ptype()==xrt::PtrType::ADDR&&t.offset()==0&&t.chunk()->byte_size==bytes&&t.dtype().bytes()==bytes&&t.data().addr()==t.chunk()->begin.addr(),"SDK owned chunk specification differs");
    return {t.data().addr(),bytes,reinterpret_cast<uintptr_t>(t.chunk().operator->())};
}
}
struct SdkScratch::Impl {''')
s=replace(s,'xrt::Tensor padding;','xrt::Tensor padding,prefix;std::filesystem::path evidence;')
s=replace(s,'need(!std::filesystem::exists(out),"Preserve typed SDK evidence");','evidence=out;need(!std::filesystem::exists(out),"Preserve typed SDK evidence");')
needle='        std::ofstream f(out/"regions.json");'
assert needle in s
s=s.replace(needle,'''        const auto pool=snapshot(region,out/"manager-before.json",0);pc::validatePool(pool,{});
        need(pool.start==4096&&pool.bytes==4294963200,"Audited public capacity changed");
        prefix=xrt::Tensor(xir::TensorType(xir::FloatType::FP32(),{int64_t(pc::prefixBytes/4)},xir::Layout("C"))).mallocOn(region);
        snapshot(region,out/"manager-prefix.json",1);
        std::ofstream f(out/"regions.json");''',1)
s=replace(s,'        const auto a=source[0].data().addr(),b=source[1].data().addr();','''        const auto occupied=block(prefix,region,pc::prefixBytes),aBlock=block(source[0],region,pose::scratch::sizes[0]),padBlock=block(padding,region,32),bBlock=block(source[1],region,pose::scratch::sizes[1]);
        snapshot(region,out/"manager-allocated.json",4);pc::validateAllocated(pool,occupied,aBlock,padBlock,bBlock);
        std::ofstream position(out/"position.json");position<<"{\\"prefix_bytes\\":"<<pc::prefixBytes<<",\\"prefix_address\\":"<<occupied.start<<",\\"prefix_chunk_identity\\":"<<occupied.identity<<",\\"source_lower\\":"<<pc::sourceLower<<",\\"source_upper_exclusive\\":"<<pc::sourceUpper<<",\\"position_controlled\\":true,\\"prefix_read_write_copy_calls\\":0,\\"explicit_address_allocation\\":false}\\n";position.close();need(bool(position),"Position evidence save failed");
        const auto a=source[0].data().addr(),b=source[1].data().addr();''')
needle='    }\n};\nSdkScratch::SdkScratch'
s=replace(s,needle,'''    }
    ~Impl(){
        try{
            source={};padding=xrt::Tensor{};prefix=xrt::Tensor{};
            snapshot(device.defaultMemRegion(),evidence/"manager-released.json",0);
        }catch(const std::exception&e){try{std::ofstream(evidence/"release.error.txt")<<e.what();}catch(...){} }
    }
};
SdkScratch::SdkScratch''')
put('software/pose_v1/src/plddr_position_sdk_r1.cpp',s)
cm=(root/'tools/pose-v1/typed-scratch-CMakeLists.txt').read_text(encoding='utf-8')+'''
add_executable(pose_position_scratch_check typed_scratch_check.cpp typed_scratch_pattern.cpp plddr_position_sdk.cpp plddr_position_contract.cpp scratch_copy_pattern.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp invocation_evidence.cpp)
target_include_directories(pose_position_scratch_check PRIVATE .)
target_link_libraries(pose_position_scratch_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_position_scratch_check PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
add_executable(pose_plddr_position_selftest plddr_position_selftest.cpp plddr_position_contract.cpp)
target_include_directories(pose_plddr_position_selftest PRIVATE .)
target_compile_options(pose_plddr_position_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
put('tools/pose-v1/plddr-position-CMakeLists.txt',cm)
builder=(root/'tools/pose-v1/Build-TypedScratch.ps1').read_text(encoding='utf-8').replace('mixed-20261010-typed-scratch-r1','mixed-20261010-plddr-position-r1')
builder=replace(builder,"'pose_typed_scratch_selftest','--parallel'","'pose_typed_scratch_selftest','pose_position_scratch_check','pose_plddr_position_selftest','--parallel'")
builder=replace(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_position_scratch_check'),(Join-Path $poseOutput 'pose_position_scratch_check'))\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_plddr_position_selftest'),(Join-Path $poseOutput 'pose_plddr_position_selftest'))\n$poseHashes = [ordered]@{}")
builder=replace(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    position_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_position_scratch_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    position_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_plddr_position_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-PlddrPosition.ps1',builder)
review=(root/'tools/pose-v1/review_typed_build.py').read_text(encoding='utf-8').replace('Build-TypedScratch.ps1','Build-PlddrPosition.ps1')
review=replace(review,"'typed_frozen_helpers')","'typed_frozen_helpers','position_frozen_sources')")
put('tools/pose-v1/review_position_build.py',review)
base=root/'.local/pose-v1-typed-scratch/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json');m['position_frozen_sources']={rel:item['sha256'] for rel,item in m['build_files'].items()}
old='tools/pose-v1/typed-scratch-CMakeLists.txt';new='tools/pose-v1/plddr-position-CMakeLists.txt';m['build_files'].pop(old);m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(root/new))
for rel,dest in {'software/pose_v1/src/plddr_position_sdk_r1.cpp':'plddr_position_sdk.cpp','software/pose_v1/include/plddr_position_contract.hpp':'plddr_position_contract.hpp','software/pose_v1/src/plddr_position_contract.cpp':'plddr_position_contract.cpp','software/pose_v1/src/plddr_position_selftest.cpp':'plddr_position_selftest.cpp'}.items():m['build_files'][rel]=dict(destination=dest,sha256=g.sha(root/rel))
for name in ['prepare_plddr_position_r1.py','Build-PlddrPosition.ps1','review_position_build.py','run-position-scratch.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-PlddrPosition.ps1';m['plddr_position']=dict(prefix_bytes=96*1024*1024,source_lower=64*1024*1024,source_upper_exclusive=128*1024*1024,manager_audit_sha256=g.sha(e/'manager.acceptance.json'),stages=['contracts','dynamic','vpu'],prefix_data_operations=0)
out=root/'.local/pose-v1-plddr-position/package-20261010-r1';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
