#include "producer_count_observation.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
namespace {void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}}
int main(int argc,char**argv){try{
    namespace p=pose::producer_count;namespace fs=std::filesystem;
    need(argc==2&&!fs::exists(argv[1]),"producer-selftest FRESH-OUTPUT");fs::path out=argv[1];fs::create_directory(out);unsigned rejected=0;
    auto reject=[&](auto test){try{test();}catch(const std::exception&){++rejected;return;}throw std::runtime_error("Missing producer refusal");};
    const std::array<p::Point,4> points{p::Point::BeforeWait,p::Point::AfterWait,p::Point::BeforeCopy,p::Point::AfterCopy};
    auto source=[](size_t slot){return p::Source{slot?8631:8629,4096+slot*32768,0,slot?16800u:30240u,slot?16800u:30240u,"ADDR","test_region"};};
    auto complete=[&](p::Recorder& recorder,uint64_t invocation){for(size_t slot=0;slot<2;++slot)for(auto point:points)recorder.sample(100000+invocation,invocation,slot,point,source(slot),[]{return 234u;});};
    p::Recorder success;size_t queries=0;std::array<uint32_t,8> values{223,233,233,234,234,234,234,234};
    for(size_t slot=0;slot<2;++slot)for(auto point:points)success.sample(100000,0,slot,point,source(slot),[&]{return values[queries++];});
    need(success.size()==8&&queries==8,"Producer query coverage differs");success.save(out/"observations");
    reject([&]{success.save(out/"observations");});
    reject([&]{p::Recorder r;r.sample(1,0,2,points[0],source(0),[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,p::Point(4),source(0),[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,points[0],source(0),{});});
    reject([&]{p::Recorder r;auto s=source(0);s.producer=8631;r.sample(1,0,0,points[0],s,[]{return 234u;});});
    reject([&]{p::Recorder r;auto s=source(0);s.capacity=1;r.sample(1,0,0,points[0],s,[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,points[1],source(0),[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,points[0],source(0),[]{return 234u;});r.sample(2,0,0,points[1],source(0),[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,points[0],source(0),[]{return 234u;});auto s=source(0);++s.address;r.sample(1,0,0,points[1],s,[]{return 234u;});});
    p::Recorder regression;regression.sample(1,0,0,points[0],source(0),[]{return 234u;});reject([&]{regression.sample(1,0,0,points[1],source(0),[]{return 233u;});});regression.save(out/"regression");
    reject([&]{p::Recorder r;r.sample(1,0,0,points[0],source(0),[]{return 746u;});});
    reject([&]{p::Recorder r;complete(r,3);r.sample(1,2,0,points[0],source(0),[]{return 234u;});});
    reject([&]{p::Recorder r;r.sample(1,0,0,points[0],source(0),[]{return 234u;});r.sample(2,1,0,points[0],source(0),[]{return 234u;});});
    p::Recorder queryError;bool original=false;try{queryError.sample(1,0,0,points[0],source(0),[]{throw std::runtime_error("Original query error");return 234u;});}catch(const std::runtime_error&e){original=std::string(e.what())=="Original query error";}need(original,"Query error replaced");queryError.save(out/"query-error");
    reject([&]{queryError.sample(1,0,0,points[1],source(0),[]{return 234u;});});
    p::Recorder bounded;for(size_t i=0;i<103;++i)complete(bounded,i);need(bounded.size()==824,"Producer row bound differs");reject([&]{complete(bounded,103);});
    p::Recorder owner;bool refused=false;std::thread other([&]{try{owner.sample(1,0,0,points[0],source(0),[]{return 234u;});}catch(const std::exception&){refused=true;}});other.join();need(refused,"Producer owner changed silently");++rejected;
    std::cout<<"{\"status\":\"passed\",\"refusals\":"<<rejected<<",\"queries_per_call\":8,\"maximum_rows\":824,\"below_target_before_copy_allowed\":true,\"query_error_preserved\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
