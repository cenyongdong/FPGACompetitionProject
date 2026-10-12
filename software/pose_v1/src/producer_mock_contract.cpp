// Isolated public SDK mock deployment. No physical URL and no forward call.
#include <icraft-xrt/core/session.h>
#include <icraft-backends/zg330backend/zg330backend.h>
#include "mixed_fusion_baseline.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <set>
namespace {
namespace xir=icraft::xir;
namespace xrt=icraft::xrt;
namespace fs=std::filesystem;
void require(bool ok,const char* message){if(!ok){throw std::runtime_error(message);}}
}
int main(int argc,char**argv){try{
    require(argc==4,"GRAPH RAW FRESH-OUTPUT required");
    const fs::path out(argv[3]);require(!fs::exists(out),"Preserve previous evidence");fs::create_directory(out);
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);graph.lazyLoadParamsFromFile(argv[2],true);
    const auto& members=pose_v1::fusion_baseline::members.at(9186);
    auto selected=graph.view(members);require(selected->ops.size()==19,"Original selected group differs");
    std::set<int64_t> inputs,outputs;
    for(const auto& v:selected.inputs()){inputs.insert(v->v_id);}
    for(const auto& v:selected.outputs()){outputs.insert(v->v_id);}
    require(inputs==std::set<int64_t>{486,478} && outputs==std::set<int64_t>{4386,4390},"Original boundary differs");
    // Documented mock:// has memory allocation only, and cannot forward.
    auto device=xrt::Device::Open("mock://zg330");
    auto session=xrt::Session::Create<xrt::zg330::ZG330Backend>(selected,{device});
    require(session.backendBindings().size()==19,"Initial binding coverage differs");
    session.enableTimeProfile(false);session.apply();
    const auto bindings=session.backendBindings();require(bindings.size()==1,"Selected group not independently fused");
    const auto& entry=*bindings.begin();require(entry.second.is<xrt::zg330::ZG330Backend>(),"Wrong backend");
    auto backend=entry.second.cast<xrt::zg330::ZG330Backend>();
    auto info=backend->forward_info;require(info.defined(),"Public ForwardInfo unavailable");
    const auto it=info->hardop_map.find(entry.first);require(it!=info->hardop_map.end() && it->second.defined(),"Fused group absent");
    const auto& fused=it->second;
    std::set<int64_t> actual(fused->merge_from.begin(),fused->merge_from.end());
    require(actual==std::set<int64_t>(members.begin(),members.end()),"Fused member identity differs");
    require(fused->sync_idx==std::pair<int,int>{0,11},"Independent synchronization scope differs");
    require(info->idx_map.at(entry.first)==fused->sync_idx,"Public sync maps disagree");
    std::ofstream report(out/"mock-contract.json");require(bool(report),"Cannot save contract");
    report<<"{\"status\":\"public_mock_selected_group_deployed\",\"URL\":\"mock://zg330\",\"physical_device_opened\":false,\"NPU_executed\":false,\"forward_called\":false,\"group\":"<<entry.first
          <<",\"sync_start\":"<<fused->sync_idx.first<<",\"layers\":"<<fused->sync_idx.second<<",\"members\":[";
    bool first=true;for(auto id:actual){if(!first){report<<',';}first=false;report<<id;}
    report<<"],\"boundary\":[";first=true;
    for(auto id:{486,478,4386,4390}){
        const auto v=info->value_map.at(id);require(v.defined(),"Boundary mapping unavailable");
        if(!first){report<<',';}first=false;
        report<<"{\"value\":"<<id<<",\"bytes\":"<<v->byte_size<<",\"logical\":"<<v->logic_addr<<",\"mock_physical\":"<<v->phy_addr
              <<",\"is_ocm\":"<<(v->is_ocm?"true":"false")<<",\"real\":"<<(v->real?"true":"false")<<'}';
    }
    report<<"]}\n";report.close();require(bool(report),"Incomplete contract");
    backend.log();std::cout<<"Mock-only selected group deployment complete; no physical device or forward.\n";
    return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
