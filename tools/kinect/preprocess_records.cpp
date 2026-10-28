#include "preprocess.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
static unsigned u32(const unsigned char*p){return unsigned(p[0])|(unsigned(p[1])<<8)|(unsigned(p[2])<<16)|(unsigned(p[3])<<24);}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("Usage: preprocess_records INPUT.piwcsi2 NEW_TOKENS.f32");
 if(std::filesystem::exists(argv[2]))throw std::runtime_error("Output exists");
 std::ifstream source(argv[1],std::ios::binary);if(!source)throw std::runtime_error("Missing input");
 std::ofstream target(argv[2],std::ios::binary);std::array<unsigned char,86432> record{};std::size_t count=0;
 while(source.read(reinterpret_cast<char*>(record.data()),record.size())){
  if(std::memcmp(record.data(),"PIWCSI2\0",8)||u32(record.data()+8)!=2||u32(record.data()+12)!=86400)throw std::runtime_error("Invalid CSI record");
  pose_v1::RawCsi raw;
  for(unsigned r=0;r<3;++r)for(unsigned a=0;a<3;++a)for(unsigned t=0;t<20;++t)for(unsigned n=0;n<30;++n){
   const auto offset=32+(((r*3+a)*20+t)*30+n)*16;double re,im;
   std::memcpy(&re,record.data()+offset,8);std::memcpy(&im,record.data()+offset+8,8);
   raw[pose_v1::raw_index(r,a,n,t)]={re,im};
  }
  const auto tokens=pose_v1::preprocess(raw);target.write(reinterpret_cast<const char*>(tokens.data()),sizeof(tokens));++count;
 }
 if(source.gcount()!=0)throw std::runtime_error("Truncated CSI record");
 if(!target)throw std::runtime_error("Feature write failed");std::cout<<"windows="<<count<<" original_preprocess=true\n";
 return count?0:3;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
