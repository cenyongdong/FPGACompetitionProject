#include <icraft-xrt/core/device.h>
#include <fstream>
#include <iomanip>
#include <filesystem>
#include <iostream>
#include <stdexcept>
namespace {
void need(bool ok,const char* message){if(!ok){throw std::runtime_error(message);}}
}
int main(int argc,char**argv){
    try{
        need(argc==3&&std::string(argv[2])=="--allow-device-init","Expected fresh output and explicit device permission");
        std::filesystem::path out(argv[1]);need(!std::filesystem::exists(out),"Preserve existing evidence");std::filesystem::create_directory(out);
        namespace xrt=icraft::xrt;namespace xir=icraft::xir;
        {
            auto device=xrt::Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000");device.setWaitTime(10000);
            auto versions=device.version();need(versions.at("device")=="25122301"&&versions.at("icore")=="FMSHZGV3TECH-AID - 24160628","Device version changed");
            auto region=device.defaultMemRegion();auto manager=region.memManager();
            need(region.device().same_as(device)&&std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Region identity changed");
            const auto&info=manager.getMemRegionInfo();const auto chunks=manager.getAllMemChunk();
            std::ofstream f(out/"manager.json");
            f<<"{\"manager_type\":"<<std::quoted(std::string(manager->typeKey()))<<",\"region_type\":"<<std::quoted(std::string(region->typeKey()))<<",\"region_identity\":"<<reinterpret_cast<uintptr_t>(region.operator->())<<",\"manager_identity\":"<<reinterpret_cast<uintptr_t>(manager.operator->())<<",\"device_owned\":true,\"full_model_Session\":false,\"NPU_forward\":false,\"Tensor_malloc_calls\":0,\"info\":{";
            bool first=true;for(const auto& item:info){if(!first){f<<',';}first=false;f<<std::quoted(item.first)<<":{"<<"\"type\":"<<std::quoted(std::string(item.second->typeKey()))<<",\"text\":"<<std::quoted(item.second.toString())<<'}';}
            f<<"},\"chunks\":[";first=true;for(const auto&chunk:chunks){if(!first){f<<',';}first=false;f<<"{\"identity\":"<<reinterpret_cast<uintptr_t>(chunk.operator->())<<",\"region_same\":"<<(chunk->region.same_as(region)?"true":"false")<<",\"ptype\":"<<int(chunk->begin.ptype())<<",\"address\":"<<chunk->begin.addr()<<",\"bytes\":"<<chunk->byte_size<<'}';}
            f<<"]}\n";f.close();need(bool(f),"Cannot save manager information");
            need(std::string(manager->typeKey())=="icraft::xrt::DefaultMemManagerNode","Allocation manager semantics not confirmed");
            need(info.count("start")&&info.count("byte_size"),"Public capacity fields absent");
            const auto*startNode=info.at("start").as<xrt::MemPtrNode>();const auto*sizeNode=info.at("byte_size").as<xir::IntImmNode>();
            need(startNode&&sizeNode&&sizeNode->value>0,"Public capacity field types unsupported");
            auto start=xir::Downcast<xrt::MemPtr>(info.at("start"));need(start.ptype()==xrt::PtrType::ADDR,"Pool is not device address space");
            auto capacity=uint64_t(sizeNode->value);need(start.addr()<=UINT64_MAX-capacity,"Public pool range overflows");
            need(chunks.empty(),"Unexpected pre-existing allocation; preserve and stop");
            std::ofstream bounds(out/"bounds.json");bounds<<"{\"start\":"<<start.addr()<<",\"capacity\":"<<capacity<<",\"end_exclusive\":"<<start.addr()+capacity<<",\"initial_chunks\":0,\"large_allocation_executed\":false}\n";bounds.close();need(bool(bounds),"Cannot save bounds");
        }
        std::ofstream(out/"closed.json")<<"{\"SDK_scope_destroyed\":true}\n";
        std::cout<<"Public manager audit completed; no Tensor allocation or model execution.\n";return 0;
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
