#pragma once
// Test double for the public SDK calls used by hdmi_output.cpp. Never linked
// into an SDK target; models explicit-free allocation and injected failures.
#include <cstdint>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
namespace icraft::xrt {
struct TestState {
    int mode=0,allocations=0,free_calls=0,duplicates=0,stop_calls=0;
    uint64_t outstanding=0;
    uint32_t sequence=0,tag=0,stopped=0;
};
inline TestState default_state;
inline TestState* test_state=&default_state;
struct MemPtr { uint64_t value; uint64_t addr()const{return value;} int ptype()const{return 1;} };
struct Chunk { MemPtr begin; uint64_t byte_size; int slot; bool freed=false; };
class MemRegion;
class MemChunk {
    std::shared_ptr<Chunk> data;
public:
    MemChunk()=default;
    MemChunk(uint64_t address,uint64_t size,int slot):data(std::make_shared<Chunk>(Chunk{{address},size,slot,false})){}
    Chunk* operator->() const{return data.get();}
    bool isOn(const MemRegion&)const{return true;}
    void free(){
        auto& s=*test_state;++s.free_calls;
        if(!data||data->freed){++s.duplicates;throw std::runtime_error("Duplicate/invalid free");}
        if(s.mode==8)throw 88;
        data->freed=true;s.outstanding-=data->byte_size;
        if(s.mode==5&&data->slot==1)throw 55; // Exception AFTER allocator mutation.
    }
    void read(char*,uint64_t,uint64_t)const{}
    void write(uint64_t,char*,uint64_t)const{}
};
class MemRegion {
public:
    const MemRegion* operator->()const{return this;}
    const char* typeKey()const{return "AXIZG330AIUdmaMemRegionNode";}
    MemChunk malloc(uint64_t size,bool auto_free,uint64_t)const{
        auto& s=*test_state;
        if(auto_free)throw std::runtime_error("Test expects explicit-free ownership");
        ++s.allocations;
        if(s.mode==9||(s.allocations==2&&(s.mode==1||s.mode==8)))throw std::runtime_error("Injected allocation failure");
        if(s.mode==3&&s.allocations==2)throw 33;
        s.outstanding+=size;
        auto address=0x30100000ull+(s.allocations-1)*0x400000ull;
        if(s.mode==2&&s.allocations==2)address=0x40000000ull;
        if(s.mode==4)address=0x30100000ull;
        return MemChunk(address,size,s.allocations);
    }
};
struct Registers {
    uint32_t read(uint64_t a)const{
        const auto& s=*test_state;
        switch(a-0x400b0000ull){
        case 0:return 0x48444d01;case 0x40:return 0x48445301;
        case 0x44:return 148500000;case 0x48:return 742500000;
        case 0x30:return 1;case 0x24:case 0x28:return s.sequence;
        case 0x10:return 0x41;case 0x14:return s.stopped;
        default:return 0;}
    }
    void write(uint64_t a,uint32_t value)const{
        auto& s=*test_state;
        if(a==0x400b0008ull)s.tag=value;
        if(a==0x400b000cull){
            if(value==3){++s.stop_calls;if(s.mode==6)throw 66;s.stopped=s.tag;}
            ++s.sequence;
        }
    }
};
class Device {
public:
    std::map<std::string,std::string> version()const{return {{"device","25122301"},{"icore","FMSHZGV3TECH-AID - 24160628"}};}
    Registers defaultRegRegion()const{return {};}
    MemRegion getMemRegion(const char*)const{return {};}
};
}
