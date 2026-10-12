"""Caller-owned partial capture survives SDK exceptions; aligned r2 stays frozen."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=root/'.local/pose-v1-scratch-copy/package-20261010-r2';g.verify(base);m=g.load(base/'manifest.json')
h=change(read('software/pose_v1/include/scratch_copy_pattern.hpp'),'void savePair(', 'void saveAvailable(const Pair&,const std::filesystem::path& freshDirectory);\nvoid savePair(');put('software/pose_v1/include/scratch_copy_pattern_r3.hpp',h)
cpp=read('software/pose_v1/src/scratch_copy_pattern.cpp')
cpp=change(cpp,'void savePair(','''void saveAvailable(const Pair& pair,const std::filesystem::path& dir){
    for(size_t i=0;i<2;++i)need(pair.values[i].empty()||pair.values[i].size()==sizes[i],"Scratch partial pair size differs");
    need(!dir.empty()&&!std::filesystem::exists(dir),"Preserve partial scratch pair");std::filesystem::create_directory(dir);std::ofstream index(dir/"identity.json");
    index<<"{\\"source\\":\\"owned_bytes\\",\\"partial\\":"<<(pair.values[0].empty()||pair.values[1].empty()?"true":"false")<<",\\"slots\\":[";bool first=true;
    for(size_t i=0;i<2;++i){if(pair.values[i].empty())continue;const auto name=std::string(i?"b.f32":"a.f32");std::ofstream f(dir/name,std::ios::binary);f.write(pair.values[i].data(),pair.values[i].size());f.close();need(bool(f),"Scratch partial bytes save failed");
        if(!first)index<<',';
        first=false;index<<"{\\"slot\\":"<<i<<",\\"bytes\\":"<<sizes[i]<<",\\"fnv1a64\\":"<<fingerprint(pair.values[i])<<",\\"file\\":\\""<<name<<"\\"}";
    }index<<"]}\\n";index.close();need(bool(index),"Scratch partial index failed");
}
void savePair(''');put('software/pose_v1/src/scratch_copy_pattern_r3.cpp',cpp)
test=change(read('software/pose_v1/src/scratch_copy_pattern_selftest.cpp'),'    std::cout<<','''    s::Pair partial;partial.values[0]=valid.values[0];s::saveAvailable(partial,out/"partial-after-exception");need(!fs::exists(out/"partial-after-exception/b.f32"));
    reject([&]{s::saveAvailable(partial,out/"partial-after-exception");});reject([&]{s::Pair p;p.values[0].resize(1);s::saveAvailable(p,out/"malformed-partial");});
    std::cout<<''');put('software/pose_v1/src/scratch_copy_pattern_selftest_r3.cpp',test)
sdkh=change(read('software/pose_v1/include/scratch_copy_sdk.hpp'),'Pair copyPair();','void copyPair(Pair& callerOwned);');put('software/pose_v1/include/scratch_copy_sdk_r3.hpp',sdkh)
sdk=read('software/pose_v1/src/scratch_copy_sdk_r2.cpp');sdk=change(sdk,'Pair SdkScratch::copyPair(){p_->check();Pair pair;','void SdkScratch::copyPair(Pair& pair){p_->check();pair=Pair{};');sdk=change(sdk,'}return pair;}\n}', '} }\n}');put('software/pose_v1/src/scratch_copy_sdk_r3.cpp',sdk)
entry=change(read('software/pose_v1/src/scratch_copy_check_r1.cpp'),'current=sdk->copyPair();hasCurrent=true;', 'hasCurrent=true;sdk->copyPair(current);')
entry=change(entry,'if(failure&&hasCurrent){try{s::savePair(current,out/"failed-pair");}catch(...){}if(sdk)', 'if(failure){if(hasCurrent)try{s::saveAvailable(current,out/"failed-pair");}catch(const std::exception&e){std::ofstream(out/"failure-capture.error.txt")<<e.what();}if(sdk)')
put('software/pose_v1/src/scratch_copy_check_r3.cpp',entry)
builder=read('tools/pose-v1/Build-ScratchCopyR2.ps1').replace('mixed-20261010-scratch-copy-r2','mixed-20261010-scratch-copy-r3');put('tools/pose-v1/Build-ScratchCopyR3.ps1',builder)
review=read('tools/pose-v1/review_scratch_host_r2.py').replace('Build-ScratchCopyR2.ps1','Build-ScratchCopyR3.ps1');review=change(review,"'scratch_r2_frozen_sources')","'scratch_r2_frozen_sources','scratch_r3_frozen_sources')");put('tools/pose-v1/review_scratch_host_r3.py',review)
mapping={'software/pose_v1/include/scratch_copy_pattern.hpp':'software/pose_v1/include/scratch_copy_pattern_r3.hpp','software/pose_v1/src/scratch_copy_pattern.cpp':'software/pose_v1/src/scratch_copy_pattern_r3.cpp','software/pose_v1/src/scratch_copy_pattern_selftest.cpp':'software/pose_v1/src/scratch_copy_pattern_selftest_r3.cpp','software/pose_v1/include/scratch_copy_sdk.hpp':'software/pose_v1/include/scratch_copy_sdk_r3.hpp','software/pose_v1/src/scratch_copy_sdk_r2.cpp':'software/pose_v1/src/scratch_copy_sdk_r3.cpp','software/pose_v1/src/scratch_copy_check_r1.cpp':'software/pose_v1/src/scratch_copy_check_r3.cpp'}
m['scratch_r3_frozen_sources']={rel:g.sha(root/rel) for rel in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
for name in ('prepare_scratch_copy_r3.py','Build-ScratchCopyR3.ps1','review_scratch_host_r3.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ScratchCopyR3.ps1';m['scratch_copy']['caller_owned_partial_capture']=True;m['scratch_copy']['late_sources_after_any_SDK_exception']=True
out=root/'.local/pose-v1-scratch-copy/package-20261010-r3';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
