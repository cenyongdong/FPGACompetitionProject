// Paired offline preprocessing. Raw and identities are independent of labels.
#include "software/core/input/phase_branch.hpp"
#include <cstring>
#include <fstream>
#include <iostream>

namespace {
void need(bool v,const char* s){if(!v)throw std::runtime_error(s);}
std::uint64_t little(const unsigned char* p,std::size_t size){std::uint64_t n=0;for(std::size_t i=0;i<size;++i)n|=std::uint64_t(p[i])<<(8*i);return n;}
}
int main(int argc,char** argv) {
    try {
        need(argc==5,"Usage: phase_preprocess raw.piwcsi2 identities.bin original.f32 continuous.f32");
        std::ifstream raw(argv[1],std::ios::binary),identities(argv[2],std::ios::binary);
        need(bool(raw)&&bool(identities),"Cannot open paired preprocessing inputs");
        for(int i:{3,4}){std::ifstream old(argv[i]);need(!old,"Refusing to overwrite preprocessing outputs");}
        std::ofstream original(argv[3],std::ios::binary),continuous(argv[4],std::ios::binary);
        need(bool(original)&&bool(continuous),"Cannot create preprocessing outputs");
        pose_v1::PhaseBranchTracker tracker;std::uint64_t frames=0,rotated=0,undefined=0;
        std::array<unsigned char,86432> bytes{};std::array<unsigned char,1440> stamps{};
        while(raw.read(reinterpret_cast<char*>(bytes.data()),bytes.size())||raw.gcount()) {
            need(raw.gcount()==std::streamsize(bytes.size()),"Truncated raw record");
            need(!std::memcmp(bytes.data(),"PIWCSI2\0",8)&&little(bytes.data()+8,4)==2&&little(bytes.data()+12,4)==86400,"Invalid raw record");
            identities.read(reinterpret_cast<char*>(stamps.data()),stamps.size());need(identities.gcount()==std::streamsize(stamps.size()),"Missing source identities");
            pose_v1::RawCsi csi;
            for(std::size_t r=0;r<3;++r)for(std::size_t a=0;a<3;++a)for(std::size_t t=0;t<20;++t)for(std::size_t n=0;n<30;++n) {
                const auto at=32+(((r*3+a)*20+t)*30+n)*16;
                auto re=little(bytes.data()+at,8),im=little(bytes.data()+at+8,8);double x,y;
                std::memcpy(&x,&re,8);std::memcpy(&y,&im,8);csi[pose_v1::raw_index(r,a,n,t)]={x,y};
            }
            const auto old=pose_v1::preprocess(csi);pose_v1::PhaseHints hints{};
            for(std::size_t r=0;r<3;++r)for(std::size_t t=0;t<20;++t) {
                const auto at=(r*20+t)*24;std::array<std::complex<double>,3> z;
                for(std::size_t a=0;a<3;++a)z[a]=csi[pose_v1::raw_index(r,a,0,t)];
                const auto h=tracker.observe(r,z,{little(stamps.data()+at,8),little(stamps.data()+at+8,8),std::int64_t(little(stamps.data()+at+16,8))});
                hints[r][t]=h.rotation;rotated+=bool(h.rotation);undefined+=!h.defined;
            }
            const auto changed=pose_v1::apply_phase_branches(old,hints);
            original.write(reinterpret_cast<const char*>(old.data()),sizeof(old));continuous.write(reinterpret_cast<const char*>(changed.data()),sizeof(changed));++frames;
        }
        need(identities.peek()==EOF,"Trailing source identities");need(!raw.bad()&&bool(original)&&bool(continuous),"Paired preprocessing I/O failed");
        std::uint64_t resets=0,changes=0,reused=0;
        for(std::size_t r=0;r<3;++r){auto d=tracker.diagnostics(r);resets+=d.resets;changes+=d.branch_changes;reused+=d.reused;}
        std::cout<<"{\"frames\":"<<frames<<",\"rotated_rx_samples\":"<<rotated<<",\"undefined_references\":"<<undefined
                 <<",\"branch_changes\":"<<changes<<",\"resets\":"<<resets<<",\"reused_events\":"<<reused<<",\"SDK\":false}\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
