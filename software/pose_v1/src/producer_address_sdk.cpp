#include "producer_address_sdk.hpp"
#include <fstream>
#include <thread>
#include <stdexcept>
namespace pose::producer_address {
namespace {
namespace xrt=icraft::xrt;namespace xir=icraft::xir;
void need(bool x,const char*m){if(!x){throw std::runtime_error(m);}}
Block block(const xrt::MemChunk&c,const xrt::MemRegion&r){need(c.defined()&&c->region.same_as(r)&&c->begin.ptype()==xrt::PtrType::ADDR,"Prefix chunk region/pointer differs");return {c->begin.addr(),c->byte_size,reinterpret_cast<uintptr_t>(c.operator->())};}
void write(const std::filesystem::path&p,const std::string&s){need(!std::filesystem::exists(p),"Preserve address evidence");std::ofstream f(p);f<<s;f.close();need(bool(f),"Address evidence save failed");}
}
struct Reservation::Impl {
    xrt::MemRegion region;xrt::MemChunk prefix;Pool pool{};std::thread::id owner=std::this_thread::get_id();
    void check()const{need(owner==std::this_thread::get_id(),"Prefix owner changed");}
    explicit Impl(const xrt::Device&device){
        region=device.defaultMemRegion();need(region.device().same_as(device)&&std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Prefix region identity differs");
        auto manager=region.memManager();need(std::string(manager->typeKey())=="icraft::xrt::DefaultMemManagerNode","Prefix manager differs");const auto&info=manager.getMemRegionInfo();
        need(info.count("start")&&info.count("byte_size"),"Public region bounds absent");
        const auto* start=info.at("start").as<xrt::MemPtrNode>();const auto* size=info.at("byte_size").as<xir::IntImmNode>();
        need(start&&size&&size->value>0,"Unsupported public bounds");auto ptr=xir::Downcast<xrt::MemPtr>(info.at("start"));need(ptr.ptype()==xrt::PtrType::ADDR,"Public pool is not ADDR");pool={ptr.addr(),static_cast<uint64_t>(size->value)};
        need(manager.getAllMemChunk().empty(),"Unexpected pre-Session chunks");validatePool(pool,{});
        // Automatic SDK allocation only; no caller-specified address or data access.
        prefix=region.malloc(prefixBytes,true,4096);validatePrefix(pool,block(prefix,region));
    }
};
Reservation::Reservation(const xrt::Device&device,const std::filesystem::path&out):p_(std::make_unique<Impl>(device)){
    auto b=block(p_->prefix,p_->region);write(out/"prefix.json","{\"pool_start\":"+std::to_string(p_->pool.start)+",\"declared_capacity\":"+std::to_string(p_->pool.bytes)+",\"prefix_start\":"+std::to_string(b.start)+",\"prefix_bytes\":"+std::to_string(b.bytes)+",\"identity\":"+std::to_string(b.identity)+",\"auto_free\":true,\"alignment\":4096,\"read_write_copy_calls\":0,\"explicit_address_allocation\":false}\n");
}
Reservation::~Reservation()=default;
void Reservation::recordAllocated(const std::filesystem::path&out)const{
    p_->check();std::vector<Block> blocks;for(const auto&c:p_->region.memManager().getAllMemChunk()){blocks.push_back(block(c,p_->region));}validateMap(p_->pool,block(p_->prefix,p_->region),blocks);
    std::string s="{\"lower\":"+std::to_string(lower)+",\"upper_exclusive\":"+std::to_string(upper)+",\"chunks\":[";bool first=true;
    for(const auto&b:blocks){if(!first){s+=',';}first=false;s+="{\"address\":"+std::to_string(b.start)+",\"bytes\":"+std::to_string(b.bytes)+",\"identity\":"+std::to_string(b.identity)+"}";}write(out/"address-map.json",s+"]}\n");
}
void Reservation::checkBoundary(uint64_t address,uint64_t bytes,uint64_t identity)const{p_->check();validateBoundary({address,bytes,identity});}
void Reservation::release(const std::filesystem::path&out){
    p_->check();{const auto chunks=p_->region.memManager().getAllMemChunk();need(chunks.size()==1&&chunks[0].same_as(p_->prefix),"Session still owns chunks before prefix release");}
    p_->prefix=xrt::MemChunk{};need(p_->region.memManager().getAllMemChunk().empty(),"Prefix auto_free did not empty manager");write(out/"prefix-release.json","{\"after_Session_destroy\":true,\"before_prefix_drop_chunks\":1,\"after_prefix_drop_chunks\":0,\"prefix_data_access_calls\":0}\n");
}
}
