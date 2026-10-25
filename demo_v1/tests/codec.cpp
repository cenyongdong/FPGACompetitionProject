#include "aligned_csi.hpp"
#include "bounded_queue.hpp"
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>

int main(int argc, char** argv) {
    try {
        std::vector<unsigned char> bytes(demo_v1::csi_record_bytes, 0);
        std::memcpy(bytes.data(), "PIWCSI2\0", 8);
        demo_v1::put32(bytes.data()+8, 2); demo_v1::put32(bytes.data()+12, 86400);
        demo_v1::put64(bytes.data()+16, 42); demo_v1::put64(bytes.data()+24, 999);
        for (size_t i=0; i<5400; ++i) {
            double re=double(i), im=-double(i);
            std::memcpy(bytes.data()+32+i*16,&re,8); std::memcpy(bytes.data()+40+i*16,&im,8);
        }
        auto decoded=demo_v1::decode_aligned(bytes);
        for(size_t r=0;r<3;++r) for(size_t a=0;a<3;++a) for(size_t t=0;t<20;++t) for(size_t n=0;n<30;++n) {
            const auto source=((r*3+a)*20+t)*30+n;
            if(decoded.csi[pose_v1::raw_index(r,a,n,t)] != std::complex<double>(double(source),-double(source))) throw std::runtime_error("Axis mapping failed");
        }
        auto rejects=[&] { try { demo_v1::decode_aligned(bytes); } catch(const std::exception&) { return; } throw std::runtime_error("Bad record accepted"); };
        bytes[8]=1; rejects(); bytes[8]=2;
        double nan=std::numeric_limits<double>::quiet_NaN(); std::memcpy(bytes.data()+32,&nan,8); rejects();
        bytes.pop_back(); rejects();
        demo_v1::Queue<int> queue(1); queue.push(1);
        bool overflow=false; try {queue.push(2);} catch(const std::exception&) {overflow=true;}
        if(!overflow || *queue.pop()!=1) throw std::runtime_error("Queue overwrote input");
        queue.close(); if(queue.pop()) throw std::runtime_error("Queue EOF failed");
        demo_v1::Queue<std::unique_ptr<int>> owned(1);
        owned.push(std::make_unique<int>(7));auto retained=std::make_unique<int>(8);
        try {owned.push(std::move(retained));}catch(const std::exception&){}
        if(!retained||*retained!=8)throw std::runtime_error("Overflow destroyed unpublished actual");
        owned.fail(std::make_exception_ptr(std::runtime_error("failure")));
        const auto evidence=owned.drain_for_evidence();
        if(evidence.size()!=1||*evidence[0]!=7)throw std::runtime_error("Pending evidence lost on failure");
        if(argc==3) {
            std::ifstream source(argv[1],std::ios::binary);
            bytes.assign(std::istreambuf_iterator<char>(source),{});
            decoded=demo_v1::decode_aligned(bytes);
            const auto tokens=pose_v1::preprocess(decoded.csi);
            std::ifstream reference(argv[2],std::ios::binary); pose_v1::Tokens expected;
            reference.read(reinterpret_cast<char*>(expected.data()),sizeof(expected));
            if(!reference || std::memcmp(tokens.data(),expected.data(),sizeof(tokens))) throw std::runtime_error("Frozen preprocessing mismatch");
        }
        std::cout << "Axis/invalid records/queue and supplied frozen preprocessing passed\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
