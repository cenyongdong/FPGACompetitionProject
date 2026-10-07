// Diagnostic Host-only reads. No device reads, ready-state changes or cache controls.
#pragma once
#include "mixed_bridge.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>

namespace pose_v1::content_diagnostic {
namespace fs=std::filesystem;
namespace xrt=icraft::xrt;
inline std::mutex mutex;
inline bool active=false;
inline fs::path directory;
inline std::ofstream index;
inline uint64_t frame=0,invocation=0;
inline std::string case_name;
inline void require(bool condition,const std::string& message) {
    if(!condition)throw std::runtime_error("Host content diagnostic: "+message);
}
inline void configure(const fs::path& output) {
    std::lock_guard<std::mutex> guard(mutex);
    require(!active && !fs::exists(output),"Preserve earlier content directory");
    fs::create_directory(output);directory=output;
    index.open(output/"index.jsonl");require(bool(index),"Cannot create content index");
    index.exceptions(std::ios::failbit|std::ios::badbit);active=true;
}
inline bool enabled() { std::lock_guard<std::mutex> guard(mutex);return active; }
inline void set_context(uint64_t value_frame,uint64_t value_invocation,const std::string& name) {
    std::lock_guard<std::mutex> guard(mutex);
    require(name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")==std::string::npos,
            "Unsafe case name");
    frame=value_frame;invocation=value_invocation;case_name=name;
}
inline std::vector<char> capture(const xrt::Tensor& tensor,const std::string& kind,
                               int64_t op_id,size_t slot,const std::vector<char>* expected=nullptr,
                               const xrt::Tensor& caller={}) {
    std::lock_guard<std::mutex> guard(mutex);
    require(active,"Content capture not configured");
    require(kind.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_")==std::string::npos,"Unsafe capture kind");
    require(tensor.hasData() && tensor.isOn(xrt::HostDevice::MemRegion()) &&
            tensor.data().ptype()==xrt::PtrType::CPTR,"Only allocated Host CPTR may be captured");
    require(tensor.dtype()->element_dtype.isFP32(),"Only FP32 content may be captured");
    const auto size=tensor.dtype().bytes();
    require(size>0 && size<=1024*1024 && tensor.offset()<=tensor.chunk()->byte_size &&
            size<=tensor.chunk()->byte_size-tensor.offset(),"Invalid Host storage bounds");
    if(caller.defined())require(caller.hasData() && caller.isOn(xrt::HostDevice::MemRegion()) &&
                               caller.data().ptype()==xrt::PtrType::CPTR,"Caller identity is not Host CPTR");
    std::vector<char> raw(static_cast<size_t>(size));
    // SDK reads already-resident Host storage. Never call wait/copyTo/device read here.
    tensor.read(raw.data(),0,size);
    const auto name="call"+std::to_string(invocation)+"."+kind+".op"+std::to_string(op_id)+".slot"+std::to_string(slot)+".f32";
    require(!fs::exists(directory/name),"Duplicate content capture");
    std::ofstream data(directory/name,std::ios::binary);
    data.write(raw.data(),static_cast<std::streamsize>(raw.size()));data.close();require(bool(data),"Cannot save Host content");
    index << "{\"case\":" << std::quoted(case_name) << ",\"frame_id\":" << frame
          << ",\"invocation\":" << invocation << ",\"kind\":" << std::quoted(kind)
          << ",\"op_id\":" << op_id << ",\"slot\":" << slot << ",\"file\":" << std::quoted(name)
          << ",\"bytes\":" << raw.size() << ",\"tensor\":";
    mixed_candidate::tensor_info(index,tensor);
    if(expected)index << ",\"matches_expected\":" << (raw==*expected?"true":"false");
    if(caller.defined()) {
        index << ",\"same_handle_as_caller\":" << (tensor.same_as(caller)?"true":"false")
              << ",\"same_chunk_as_caller\":" << (tensor.chunk().same_as(caller.chunk())?"true":"false");
    }
    index << "}\n";index.flush();
    require(!expected || raw==*expected,kind+" differs from current caller tokens");
    return raw;
}
} // namespace pose_v1::content_diagnostic
