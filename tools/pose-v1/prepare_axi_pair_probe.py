"""Historical r1 source bootstrap; stopped before manifest completion.

Do not rerun this bootstrap. Current reproducible source/build entry is
build_axi_pair_probe_r4.py with the checked-in corrected modules.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'software/pose_v1/src';INC=ROOT/'software/pose_v1/include'
def fresh(path,text):
    assert not path.exists(),path
    path.write_text(text,encoding='utf-8',newline='\n')
fresh(INC/'axi_pair_probe.hpp','''#pragma once
#include "typed_scratch_pattern.hpp"
#include "typed_scratch_sdk.hpp"
#include <icraft-xrt/core/tensor.h>
namespace pose::axi_probe {
enum class Method { Copy, Read };
void transfer(const icraft::xrt::Tensor&,icraft::xrt::Tensor&,Method);
using Pair=pose::typed_scratch::Pair;
using Writes=pose::typed_scratch::Writes;
using pose::typed_scratch::pattern;
using pose::typed_scratch::matches;
using pose::typed_scratch::saveExpected;
class SdkScratch {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    SdkScratch(const std::filesystem::path&,const std::filesystem::path&,Method);
    ~SdkScratch();
    void readSources(Pair&);
    void writePattern(size_t,Writes&);
    void copyPair(Pair&);
};
}
''')
fresh(SRC/'axi_pair_transfer.cpp','''#include "axi_pair_probe.hpp"
#include "input_read_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <stdexcept>
namespace pose::axi_probe {
void transfer(const icraft::xrt::Tensor&src,icraft::xrt::Tensor&dst,Method method){
    namespace xrt=icraft::xrt;
    if(method!=Method::Copy&&method!=Method::Read)throw std::runtime_error("Unknown transfer method");
    if(!src.defined()||!dst.defined()||!src.hasData()||!dst.hasData()||src.dtype()!=dst.dtype()||
       !src.dtype()->element_dtype.isFP32()||(src.dtype().bytes()!=30240&&src.dtype().bytes()!=16800)||
       !dst.isOn(xrt::HostDevice::MemRegion())||dst.data().ptype()!=xrt::PtrType::CPTR||
       src.offset()>src.chunk()->byte_size||src.dtype().bytes()>src.chunk()->byte_size-src.offset()||
       dst.offset()>dst.chunk()->byte_size||dst.dtype().bytes()>dst.chunk()->byte_size-dst.offset()||
       src.chunk().same_as(dst.chunk()))throw std::runtime_error("Transfer storage/type/ownership differs");
    if(method==Method::Read){pose::input_read::intoHost(src,dst);}
    else{dst.copyFrom(0,src,0,size_t(src.dtype().bytes()));}
}
}
''')
sdk=(SRC/'plddr_position_sdk_r1.cpp').read_text(encoding='utf-8')
sdk=sdk.replace('#include "typed_scratch_sdk.hpp"','#include "axi_pair_probe.hpp"').replace('namespace pose::typed_scratch {','namespace pose::axi_probe {')
sdk=sdk.replace('std::thread::id owner=', 'Method method;std::thread::id owner=',1)
sdk=sdk.replace('Impl(const std::filesystem::path&graphPath,const std::filesystem::path&out){','Impl(const std::filesystem::path&graphPath,const std::filesystem::path&out,Method chosen):method(chosen){')
sdk=sdk.replace('SdkScratch::SdkScratch(const std::filesystem::path&graph,const std::filesystem::path&out):p_(std::make_unique<Impl>(graph,out)){}','SdkScratch::SdkScratch(const std::filesystem::path&graph,const std::filesystem::path&out,Method method):p_(std::make_unique<Impl>(graph,out,method)){}')
assert sdk.count('dest.copyFrom(0,p_->source[i],0,pose::scratch::sizes[i]);')==1
sdk=sdk.replace('dest.copyFrom(0,p_->source[i],0,pose::scratch::sizes[i]);','transfer(p_->source[i],dest,p_->method);')
fresh(SRC/'axi_pair_sdk.cpp',sdk)
main=(SRC/'typed_scratch_check.cpp').read_text(encoding='utf-8')
main=main.replace('#include "typed_scratch_sdk.hpp"','#include "axi_pair_probe.hpp"').replace('namespace ts=pose::typed_scratch;','namespace ts=pose::axi_probe;')
main=main.replace('const bool vpu=mode=="vpu",dynamic=mode!="static";','const bool vpu=mode=="copy-vpu"||mode=="read-vpu",dynamic=true;const auto method=mode=="read"||mode=="read-vpu"?ts::Method::Read:ts::Method::Copy;')
main=main.replace('(mode=="static"||mode=="dynamic"||vpu)','(mode=="copy"||mode=="read"||vpu)')
main=main.replace('typed static|dynamic|vpu','axi copy|read|copy-vpu|read-vpu').replace('(graph,out/"sdk")','(graph,out/"sdk",method)')
fresh(SRC/'axi_pair_check.cpp',main)
fresh(SRC/'axi_pair_host_check.cpp','''#include "axi_pair_probe.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <cstring>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{
    namespace xrt=icraft::xrt;namespace xir=icraft::xir;namespace a=pose::axi_probe;
    if(argc!=2)throw std::runtime_error("Pinned graph required");
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);size_t bytes=0,rejects=0;
    for(size_t slot=0;slot<2;++slot){auto type=graph.getOpById(192)->inputs[slot].tensorType();
        auto source=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        auto dest=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        for(size_t index:{size_t(0),size_t(1),size_t(48),size_t(100)}){
            const auto expected=pose::typed_scratch::pattern(slot,index);source.write(0,expected.data(),expected.size());
            for(auto method:{a::Method::Copy,a::Method::Read}){a::transfer(source,dest,method);
                if(dest.dtype()!=type||std::memcmp(dest.data().cptr(),expected.data(),expected.size()))throw std::runtime_error("Host result/type differs");bytes+=expected.size();}
        }
        for(auto method:{a::Method::Copy,a::Method::Read}){bool caught=false;try{a::transfer(source,source,method);}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Alias accepted");}
        bool caught=false;try{a::transfer(source,dest,static_cast<a::Method>(9));}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Unknown method accepted");
    }
    xrt::Tensor empty;for(auto method:{a::Method::Copy,a::Method::Read}){bool caught=false;try{a::transfer(empty,empty,method);}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Empty accepted");}
    if(bytes!=376320||rejects!=8)throw std::runtime_error("Host coverage differs");
    std::cout<<"{\\"status\\":\\"passed\\",\\"Host_bytes\\":376320,\\"refusals\\":8,\\"device_opened\\":false}\\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\\n';return 1;}}
''')
cmake='''cmake_minimum_required(VERSION 3.24)
project(pose_axi_pair LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)
find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
add_executable(pose_axi_pair_check axi_pair_check.cpp axi_pair_sdk.cpp axi_pair_transfer.cpp input_read_sdk.cpp input_read_contract.cpp typed_scratch_pattern.cpp plddr_position_contract.cpp scratch_copy_pattern.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp invocation_evidence.cpp)
add_executable(pose_axi_pair_host_check axi_pair_host_check.cpp axi_pair_transfer.cpp input_read_sdk.cpp input_read_contract.cpp typed_scratch_pattern.cpp scratch_copy_pattern.cpp)
foreach(target pose_axi_pair_check pose_axi_pair_host_check)
 target_include_directories(${target} PRIVATE .)
 target_link_libraries(${target} PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
 target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
endforeach()
'''
fresh(ROOT/'tools/pose-v1/axi-pair-CMakeLists.txt',cmake)
pkg=ROOT/'.local/pose-v1-axi-pair/package-20261011-r1';assert not pkg.exists();pkg.mkdir(parents=True)
old=json.loads((ROOT/'.local/pose-v1-plddr-position/package-20261010-r1/manifest.json').read_text())
files={}
for name in re.findall(r'\b\w+\.cpp\b',cmake):files['software/pose_v1/src/'+name]='scratch_copy_pattern_r3.cpp' if name=='scratch_copy_pattern.cpp' else name
# Actual source mapping, not the destination name, binds the frozen failure helper.
files.pop('software/pose_v1/src/scratch_copy_pattern.cpp');files['software/pose_v1/src/scratch_copy_pattern_r3.cpp']='scratch_copy_pattern.cpp'
headers=['axi_pair_probe.hpp','typed_scratch_sdk.hpp','typed_scratch_pattern.hpp','scratch_copy_pattern_r3.hpp','scratch_vpu_load.hpp','timed_resident_encoder.hpp','invocation_evidence.hpp','plddr_position_contract.hpp','input_read_sdk.hpp','input_read_contract.hpp']
for name in headers:files['software/pose_v1/include/'+name]='scratch_copy_pattern.hpp' if name=='scratch_copy_pattern_r3.hpp' else name
files['tools/pose-v1/axi-pair-CMakeLists.txt']='CMakeLists.txt'
files['tools/pose-v1/aarch64-toolchain.cmake']='toolchain.cmake'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'build_files':{p:{'destination':d,'sha256':sha(ROOT/p)} for p,d in files.items()},'sdk_headers_normalized_sha256':old['sdk_headers_normalized_sha256'],'host_library_sha256':old['host_library_sha256'],'zg_library_sha256':old['zg_library_sha256'],'graph_sha256':None,'no_model_execution':True}
# Reuse only the model graph for actual types, with a byte-exact hash.
graph=ROOT/'.local/pose-v1-plddr-position/package-20261010-r1/graph/piw24_ZG.json'
assert graph.exists();(pkg/'graph').mkdir();(pkg/'graph/piw24_ZG.json').write_bytes(graph.read_bytes());manifest['graph_sha256']=sha(graph)
(pkg/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Prepared isolated AXI pair sources',len(files),pkg)
