// Offline public XIR-only inspection. No XRT/backend/device dependencies.
#include <icraft-xir/core/network.h>
#include "mixed_fusion_baseline.hpp"
#include <iostream>
#include <stdexcept>
namespace {
namespace xir=icraft::xir;
void values(const xir::Array<xir::Value>&list){
    std::cout<<'[';bool first=true;
    for(const auto&v:list){if(!first){std::cout<<',';}first=false;
        std::cout<<"{\"value\":"<<v->v_id<<",\"parameter\":"<<(v.isParams()?"true":"false")<<",\"bytes\":"<<v.storageBytes()<<",\"memory\":\""<<v->mtype->typeKey()<<"\"}";
    }std::cout<<']';
}
void view(const xir::Network&graph,const std::vector<int64_t>&ids,const char*name){
    auto selected=graph.view(ids);
    std::cout<<"{\"name\":\""<<name<<"\",\"members\":[";
    for(size_t i=0;i<ids.size();++i){if(i){std::cout<<',';}std::cout<<ids[i];}
    std::cout<<"],\"inputs\":";values(selected.inputs());std::cout<<",\"outputs\":";values(selected.outputs());std::cout<<"}";
}
}
int main(int argc,char**argv){try{
    if(argc!=2){throw std::runtime_error("Pinned graph required");}
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);const auto&members=pose_v1::fusion_baseline::members.at(9186);
    if(members.size()!=19){throw std::runtime_error("Frozen fusion membership differs");}
    std::cout<<"{\"status\":\"offline_public_views_inspected\",\"Device_opened\":false,\"Session_created\":false,\"RAW_loaded\":false,\"views\":[";
    view(graph,{8629},"single_data_producer");std::cout<<',';view(graph,{8631},"single_index_producer");std::cout<<',';view(graph,members,"original_9186_members");
    std::cout<<"],\"producer_ops\":[";
    bool first=true;for(auto id:{8629,8631}){auto op=graph.getOpById(id);if(!first){std::cout<<',';}first=false;
        std::cout<<"{\"op\":"<<id<<",\"type\":\""<<op->typeKey()<<"\",\"inputs\":";values(op->inputs);std::cout<<",\"outputs\":";values(op->outputs);std::cout<<'}';}
    std::cout<<"]}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
