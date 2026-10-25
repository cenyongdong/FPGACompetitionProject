#include "host_stage_observation.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <stdexcept>
int main(int argc, char** argv) {
    if(argc!=2) return 2;
    namespace o=pose::stage_observation;
    const std::filesystem::path root(argv[1]); std::filesystem::create_directory(root);
    o::configure(root/"copy");
    for(unsigned frame=0;frame<200;++frame) {
        o::Call c(frame,frame,192);
        for(unsigned slot=0;slot<2;++slot) {
            std::array<float,4> bytes{float(frame),float(slot),2,3};
            o::Info i; i.slot=slot;i.bytes=sizeof(bytes);i.hostCapacity=sizeof(bytes);i.sourceCapacity=sizeof(bytes);
            i.hostPointer=reinterpret_cast<uintptr_t>(bytes.data());i.sourceKind="CPTR";
            i.beforeWaitCount=123;i.afterWaitCount=124;i.beforeCopyCount=125;i.afterCopyCount=126;
            c.afterCopy(i,reinterpret_cast<const char*>(bytes.data()));
            bytes.fill(-99); // Saved shadow must own the original bytes.
        }
        if(frame==199) {
            std::filesystem::create_directory(root/"failure");
            c.saveFailure(root/"failure",o::now());
        }
    }
    o::saveMetadata();
    std::array<float,4> actual{};std::ifstream f(root/"copy/199.input1.f32",std::ios::binary);
    f.read(reinterpret_cast<char*>(actual.data()),sizeof(actual));
    if(!f||actual[0]!=199||actual[1]!=1||actual[2]!=2||actual[3]!=3)throw std::runtime_error("Original shadow not preserved");
    unsigned rows=0;std::string line;std::ifstream index(root/"copy/recent.jsonl");while(std::getline(index,line))++rows;
    if(rows!=16)throw std::runtime_error("Original shadow ring not bounded");
    rows=0;std::ifstream meta(root/"copy/metadata.jsonl");while(std::getline(meta,line)) {
        ++rows;
#ifdef DEMO_D47_ISOLATION
        if(line.find("\"additional_device_queries\":0")==std::string::npos || line.find("layer_count")!=std::string::npos)
            throw std::runtime_error("Isolation must not report unobserved device counts");
#else
        if(line.find("\"after_copy_layer_count\":126")==std::string::npos)throw std::runtime_error("Count observation absent");
#endif
    }
    if(rows!=256)throw std::runtime_error("Metadata ring not bounded");
}
