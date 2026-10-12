// Offline diagnostic hashes of marked frozen Native NV12; no SDK or hardware.
#include "picture_source.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
int main(int argc,char**argv){try{
    if(argc!=3){throw std::runtime_error("REFERENCES MANIFEST");}std::filesystem::path root=argv[1];std::ifstream input(argv[2]);if(!input){throw std::runtime_error("Marker manifest missing");}
    std::map<std::string,std::vector<uint8_t>> cache;unsigned id,count=0;std::string name;
    while(input>>id>>name){if(id!=count||id>=1000||name.find('/')!=std::string::npos||name.find("..")!=std::string::npos){throw std::runtime_error("Marker reference identity invalid");}
        if(!cache.count(name)){auto& bytes=cache[name];bytes.resize(pose::video::nv12FrameBytes);std::ifstream f(root/name,std::ios::binary);f.read(reinterpret_cast<char*>(bytes.data()),bytes.size());if(!f||f.peek()!=EOF){throw std::runtime_error("Native NV12 byte count differs");}}
        auto frame=cache[name];pose::picture::markEncodedId(frame,id);std::cout<<id<<' '<<pose::picture::frameHash(frame)<<'\n';++count;
    }if(count<2){throw std::runtime_error("Marker sample coverage insufficient");}return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
