#include "upstream_boundary_sdk.hpp"
#include "upstream_boundary.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xrt/dev/zg330_device.h>
#include <chrono>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace pose::upstream_sdk {
namespace {
namespace xrt=icraft::xrt;namespace xir=icraft::xir;
std::unique_ptr<pose::upstream::Evidence> evidence;std::filesystem::path root;xrt::Device device;bool hardware=false;
struct Published {xrt::Tensor tensor;xir::TensorType declared;};std::map<int64_t,Published> published;
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
uint32_t count(){return hardware?device.cast<xrt::ZG330Device>().layerCount():0;}
void sample(const char*point,int64_t id,const Published&s,bool retained){
    const auto&t=s.tensor;need(t.hasData()&&t.dtype()==s.declared&&t.dtype()->element_dtype.isFP32(),"Boundary dtype/allocation differs");need(t.offset()<=t.chunk()->byte_size&&t.dtype().bytes()<=t.chunk()->byte_size-t.offset(),"Boundary source bounds differ");
    auto k=t.data().ptype();const bool host=t.isOn(xrt::HostDevice::MemRegion())&&k==xrt::PtrType::CPTR;need(host||(hardware&&device.defined()&&t.memRegion().device().same_as(device)&&(k==xrt::PtrType::ADDR||k==xrt::PtrType::BOTH)),"Boundary source device differs");
    pose::upstream::Sample row;row.point=point;row.value=id;std::ostringstream f;
    f<<"{\"tensor\":"<<reinterpret_cast<uintptr_t>(t.operator->())<<",\"chunk\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"region\":"<<pose::upstream::quoted(std::string(t.memRegion()->typeKey()))<<",\"device\":"<<reinterpret_cast<uintptr_t>(t.memRegion().device().operator->())<<",\"kind\":"<<pose::upstream::quoted(host?"CPTR":k==xrt::PtrType::ADDR?"ADDR":"BOTH")<<",\"address\":"<<(host?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr())<<",\"offset\":"<<t.offset()<<",\"capacity\":"<<t.chunk()->byte_size<<",\"bytes\":"<<t.dtype().bytes()<<",\"retained_producer_handle\":"<<(retained?"true":"false")<<",\"shape\":[";
    for(size_t i=0;i<s.declared->shape.size();++i){if(i)f<<',';f<<s.declared->shape[i];}f<<"],\"layout\":\"";for(size_t i=0;i<s.declared->shape.size();++i)f<<s.declared->layout.getAxisCharName(int64_t(i));f<<"\",\"distributions\":"<<s.declared->merged_distrs.size()<<'}';row.storage=f.str();
    try{row.countBefore=count();row.waitBegin=now();need(t.waitForReady(std::chrono::milliseconds(10000)),"Boundary public wait timed out");row.waitEnd=now();row.readBegin=now();need(t.dtype().bytes()==400||t.dtype().bytes()==16800,"Boundary read byte limit");row.bytes.resize(size_t(t.dtype().bytes()));t.read(row.bytes.data(),0,row.bytes.size());row.readEnd=now();row.countAfter=count();}
    catch(const std::exception&e){row.error=e.what();row.bytes.clear();row.readEnd=now();evidence->record(std::move(row));throw;}
    evidence->record(std::move(row));
}
void declaredInput(const xir::Operation&op,int64_t id){size_t hits=0;for(const auto&v:op->inputs)if(!v.isParams()&&v->v_id==id){++hits;need(published.at(id).declared==v.tensorType(),"Boundary declared input and producer dtype differ");}need(hits==1,"Boundary input value missing/duplicate");}
void retain(const xir::Operation&op,const std::vector<xrt::Tensor>&out,int64_t id,const char*point){need(out.size()==op->outputs.size(),"Boundary callback output arity differs");size_t hits=0;for(size_t i=0;i<op->outputs.size();++i)if(op->outputs[i]->v_id==id){++hits;need(!published.count(id),"Duplicate published boundary value");auto p=Published{out[i],op->outputs[i].tensorType()};published.emplace(id,p);sample(point,id,p,false);}need(hits==1,"Boundary fused output value unavailable");}
}
void configure(const std::filesystem::path&p){need(!evidence&&!std::filesystem::exists(p)&&std::filesystem::is_directory(p.parent_path()),"Preserve boundary configuration");root=p;evidence=std::make_unique<pose::upstream::Evidence>();}
void begin(uint64_t f,uint64_t i,const xrt::Device&d,bool allow){if(!evidence)return;need(!allow||d.defined(),"Boundary hardware identity required");device=d;hardware=allow;published.clear();evidence->begin(f,i);}
void pre(const xir::Operation&op){if(!evidence)return;if(op->op_id==442){declaredInput(op,4406);declaredInput(op,1137);sample("gather_pre_data",4406,published.at(4406),true);sample("gather_pre_indices",1137,published.at(1137),true);}else if(op->op_id==9189){declaredInput(op,1148);sample("zg_pre_gather",1148,published.at(1148),true);}}
void post(const xir::Operation&op,const std::vector<xrt::Tensor>&out){if(!evidence)return;if(op->op_id==437)retain(op,out,1137,"topk_indices");else if(op->op_id==9188)retain(op,out,4406,"zg_input_data");else if(op->op_id==442)retain(op,out,1148,"gather_post");else if(op->op_id==9189){retain(op,out,4414,"zg_post_base");retain(op,out,4418,"zg_post_update");}}
void save(){if(evidence)evidence->save(root);}
}
