#include "vpu_encoder.hpp"
#include <iostream>
#include <string>
#include <stdexcept>

int main(int argc,char** argv) {
    try {
        if(argc!=6) throw std::runtime_error("usage: pose_vpu_sequence_check negotiate|encode --allow-vpu-stream input.nv12 new-output-dir frame-count");
        std::string mode=argv[1];
        if(mode!="negotiate" && mode!="encode") throw std::runtime_error("unknown mode");
        pose::video::EncodeOptions options;
        options.allowVpuStream=std::string(argv[2])=="--allow-vpu-stream";
        std::string count=argv[5];
        if(count.empty() || count.size()>2 || count.find_first_not_of("0123456789")!=std::string::npos) throw std::runtime_error("invalid frame count");
        options.frameCount=static_cast<unsigned>(std::stoul(count));
        auto result=pose::video::encodeNv12File(argv[3],argv[4],options,mode=="encode");
        if(mode=="encode" && (!result.drained || result.submitted!=options.frameCount || result.returned!=options.frameCount)) throw std::runtime_error("incomplete finite encoding result");
        return 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<std::endl; return 1; }
}
