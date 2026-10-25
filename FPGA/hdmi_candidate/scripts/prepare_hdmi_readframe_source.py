"""Export one guarded two-pattern ARM diagnostic; no board operations."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[3]
import argparse
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
S=a.output.resolve();S.mkdir(parents=True,exist_ok=False)
for name in ('hdmi_output.cpp','hdmi_output.hpp','hdmi_format.hpp'):
 shutil.copyfile(R/'software/core/display'/name,S/name)
for name in ('r9_startup_observer.hpp','r9_observer_mapping.hpp','dma_probe_evidence.hpp'):
 shutil.copyfile(R/'FPGA/hdmi_candidate/software'/name,S/name)
shutil.copyfile(R/'FPGA/hdmi_candidate/software/CMakeLists-frame.txt',S/'CMakeLists.txt')
p=S/'hdmi_output.cpp';s=p.read_text()
s=s.replace('std::ofstream log;','std::ofstream log;\n        std::filesystem::path evidence_dir;')
s=s.replace('p.log.open(evidence);','p.evidence_dir=evidence.parent_path();\n        p.log.open(evidence);')
s=s.replace('std::vector<uint8_t> source(frameBytes), actual(frameBytes);','''std::vector<uint8_t> source(frameBytes), actual(frameBytes);
        auto save=[&](const std::string& name,const std::vector<uint8_t>& data) {
            const auto path=p.evidence_dir/name;
            need(!std::filesystem::exists(path),"Fresh memory evidence required");
            std::ofstream file(path,std::ios::binary);
            file.write(reinterpret_cast<const char*>(data.data()),data.size());
            file.close();need(bool(file),"Cannot retain complete memory evidence");
        };''')
s=s.replace('p.frames[i].write(0, reinterpret_cast<char*>(source.data()), source.size());','save("memory-source-"+std::to_string(i)+".bin",source);\n            p.frames[i].write(0, reinterpret_cast<char*>(source.data()), source.size());')
s=s.replace('p.frames[i].read(reinterpret_cast<char*>(actual.data()), 0, actual.size());','''try {p.frames[i].read(reinterpret_cast<char*>(actual.data()),0,actual.size());}
            catch (...) {
                const auto original=std::current_exception();
                try {save("memory-partial-after-read-exception-"+std::to_string(i)+".bin",actual);}
                catch (...) {std::cerr<<"MEMORY_EXCEPTION_EVIDENCE_FAILED"<<std::endl;}
                std::rethrow_exception(original);
            }
            save("memory-actual-"+std::to_string(i)+".bin",actual);''')
p.write_text(s)
original=(R/'FPGA/hdmi_candidate/software/frame_probe.cpp').read_text()
start=original.index('    std::vector<uint8_t> pattern(');end=original.index('\n}\n\nint main',start)
pattern=original[start:end]
source='''#include "hdmi_output.hpp"
#include "r9_startup_observer.hpp"
#include "r9_observer_mapping.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
namespace {
PATTERN
}
int main(int argc,char** argv) {
 using namespace pose::r9_startup;
 using pose::dma_probe_evidence::quoted;
 try {
  need(argc==3 && std::string(argv[1])=="--patterns","Only one bounded two-pattern run is supported");
  const std::filesystem::path out(argv[2]);
  need(out.is_absolute() && !std::filesystem::exists(out) && std::filesystem::create_directory(out),"Fresh absolute evidence directory required");
  pose::dma_probe_evidence::EvidenceLog evidence((out/"startup-and-read.jsonl").string());
  auto persist=[&](const std::string& line){evidence.stream()<<line;evidence.commit();};
  auto event=[&](const char* name){persist("{\\"event\\":"+quoted(name)+"}\\n");};
  Mapping mapping;
  auto read=[&](unsigned offset){return mapping.read(offset);};
  auto write=[&](unsigned offset,uint32_t value){mapping.write(offset,value);};
  Observer observer(read,write,persist);
  auto idle=[](){std::this_thread::sleep_for(std::chrono::milliseconds(20));};
  const auto before=observer.epoch("before_Open",2,idle);
  need(idle_healthy(before),"Abnormal pre-Open: no SDK or HDMI start");
  std::optional<icraft::xrt::Device> device;
  std::unique_ptr<pose::hdmi::Output> sink;
  try {
   const auto during=observer.epoch("during_Open",4,[&]{event("before_Device_Open");device.emplace(icraft::xrt::Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000"));event("Device_Open_returned");});
   need(return_path_healthy(during),"Abnormal return during Open: no memory transfer");
   const auto after=observer.epoch("after_Open",6,idle);
   need(idle_healthy(after),"Abnormal after Open: no memory transfer");
   device->setWaitTime(1000);
   need(device->defaultRegRegion().read(0x40584,true)==0,"Initial SDK DMA status nonzero");
   const auto frame=observer.epoch("memory_and_HDMI",8,[&]{
    sink=std::make_unique<pose::hdmi::Output>(*device,out/"hdmi.jsonl");
    sink->verifyMemory();
    for(unsigned i=0;i<2;++i) {
     auto pixels=pattern(i);
     std::ofstream raw(out/("pattern-"+std::to_string(i)+".rgb565"),std::ios::binary);
     raw.write(reinterpret_cast<const char*>(pixels.data()),pixels.size());raw.close();
     need(bool(raw),"Cannot save actual pattern source");
     sink->show(pixels,100+i);
     std::cout<<"HDMI_PATTERN_ADOPTED "<<i<<std::endl;
     for(unsigned n=0;n<80;++n){std::this_thread::sleep_for(std::chrono::milliseconds(100));sink->observe();}
    }
    sink->close();idle();
   });
   const auto& w=frame.words;
   need(w[3]==0,"Observer overflow/error flags during frames");
   for(unsigned c=0;c<6;++c)need(w[8+16*c+3]==0,"Non-OKAY AXI response during frames");
   for(unsigned c:{4u,5u})need(w[8+16*c]>0 && w[9+16*c]>0 && w[10+16*c]==w[8+16*c],"No completed HDMI/PS read bursts");
   sink.reset();
   const auto closed=observer.epoch("during_Close",10,[&]{event("before_Device_Close");device.reset();event("Device_Close_returned");});
   need(return_path_healthy(closed),"Abnormal return during Close");
   event("HDMI_READFRAME_COMPLETE");
   return 0;
  } catch(const std::exception& error) {
   std::cerr<<"HDMI_READFRAME_ORIGINAL_STOP "<<error.what()<<std::endl;
   try {persist("{\\"event\\":\\"original_stop\\",\\"error\\":"+quoted(error.what())+"}\\n");}catch(...){}
   if(sink)try {sink->close();}catch(const std::exception& stop){std::cerr<<"HDMI_RELEASE_WITHHELD "<<stop.what()<<std::endl;}
   std::_Exit(71);
  }
 }catch(const std::exception& error){std::cerr<<"HDMI_READFRAME_PREOPEN_STOP "<<error.what()<<std::endl;return 72;}
}
'''.replace('PATTERN',pattern,1)
(S/'frame_probe.cpp').write_text(source)
print('Prepared existing HDMI output with complete memory evidence and independent fixed-generation SDK/read-frame observation.')
