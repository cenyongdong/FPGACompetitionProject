#include "../diagnostics/index_oracle.hpp"
#include <cassert>
int main(){
    namespace o=pose_v1::mixed_candidate::index_oracle;
    std::array<float,100> indices{};std::array<float,4200> expanded{};
    for(size_t i=0;i<100;++i){indices[i]=float((i*7)%180);for(size_t j=0;j<42;++j)expanded[i*42+j]=indices[i];}
    o::remember(7,reinterpret_cast<const char*>(indices.data()),400);
    o::check(7,reinterpret_cast<const char*>(expanded.data()),16800);
    expanded[1056]=float(int(expanded[1056]+1)%180); // Legal integer but wrong producer value.
    bool rejected=false;try{o::check(7,reinterpret_cast<const char*>(expanded.data()),16800);}catch(const std::runtime_error&){rejected=true;}
    assert(rejected&&o::mismatches==1);
    assert(indices[1056/42]!=expanded[1056]); // Diagnostic never patches the input.
    rejected=false;try{o::check(8,reinterpret_cast<const char*>(expanded.data()),16800);}catch(const std::runtime_error&){rejected=true;}
    assert(rejected);
}
