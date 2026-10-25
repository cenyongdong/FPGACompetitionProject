#include "hdmi_output.hpp"
#include "r9_startup_observer.hpp"
#include "r9_observer_mapping.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
namespace {
    std::vector<uint8_t> pattern(unsigned index) {
        std::vector<uint8_t> frame(pose::hdmi::frameBytes);
        const uint16_t colors[2][4] = {{0xf800, 0x07e0, 0x001f, 0xffff}, {0xf81f, 0x07ff, 0xffe0, 0x0000}};
        for (unsigned y = 0; y < 1080; ++y) for (unsigned x = 0; x < 1920; ++x) {
            uint16_t v = colors[index][(x >= 960) + 2 * (y >= 540)];
            if (x < 8 || x >= 1912 || y < 8 || y >= 1072) v = 0xffff;
            const size_t offset = (size_t(y) * 1920 + x) * 2;
            frame[offset] = uint8_t(v); frame[offset + 1] = uint8_t(v >> 8);
        }
        return frame;
    }
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
  auto event=[&](const char* name){persist("{\"event\":"+quoted(name)+"}\n");};
  Mapping mapping;
  auto read=[&](unsigned offset){return mapping.read(offset);};
  auto write=[&](unsigned offset,uint32_t value){mapping.write(offset,value);};
  Observer observer(read,write,persist);
  auto idle=[](){std::this_thread::sleep_for(std::chrono::milliseconds(20));};
  const auto before=observer.epoch("before_Open",4,idle);
  need(idle_after_drain(before),"Abnormal pre-Open: no SDK or HDMI start");
  std::optional<icraft::xrt::Device> device;
  std::unique_ptr<pose::hdmi::Output> sink;
  try {
   const auto during=observer.epoch("during_Open",6,[&]{event("before_Device_Open");device.emplace(icraft::xrt::Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000"));event("Device_Open_returned");});
   need(return_path_healthy(during),"Abnormal return during Open: no memory transfer");
   const auto after=observer.epoch("after_Open",8,idle);
   need(idle_after_drain(after),"Abnormal after Open: no memory transfer");
   device->setWaitTime(1000);
   need(device->defaultRegRegion().read(0x40584,true)==0,"Initial SDK DMA status nonzero");
   const auto frame=observer.epoch("memory_and_HDMI",10,[&]{
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
   need(functional_reads_complete(frame),"Incomplete/error read bursts after bounded discard");
   for(unsigned c=0;c<6;++c)need(w[8+16*c+3]==0,"Non-OKAY AXI response during frames");
   for(unsigned c:{4u,5u})need(w[8+16*c]>0 && w[9+16*c]>0 && w[10+16*c]==w[8+16*c],"No completed HDMI/PS read bursts");
   sink.reset();
   const auto closed=observer.epoch("during_Close",12,[&]{event("before_Device_Close");device.reset();event("Device_Close_returned");});
   need(return_path_healthy(closed),"Abnormal return during Close");
   event("HDMI_READFRAME_COMPLETE");
   return 0;
  } catch(const std::exception& error) {
   std::cerr<<"HDMI_READFRAME_ORIGINAL_STOP "<<error.what()<<std::endl;
   try {persist("{\"event\":\"original_stop\",\"error\":"+quoted(error.what())+"}\n");}catch(...){}
   if(sink)try {sink->close();}catch(const std::exception& stop){std::cerr<<"HDMI_RELEASE_WITHHELD "<<stop.what()<<std::endl;}
   std::_Exit(71);
  }
 }catch(const std::exception& error){std::cerr<<"HDMI_READFRAME_PREOPEN_STOP "<<error.what()<<std::endl;return 72;}
}
