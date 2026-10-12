#include "producer_sdk.hpp"
#include <chrono>
#include <iostream>
#include <thread>
int main(int argc,char**argv){
    using namespace pose::producer;namespace fs=std::filesystem;using Clock=std::chrono::steady_clock;
    fs::path out;
    try{
        need(argc==7,"MODE GRAPH RAW PATTERNS FRESH-OUTPUT explicit-mode-flag required");
        const bool mock=std::string(argv[1])=="mock";need(mock||std::string(argv[1])=="physical","Unknown mode");
        need(std::string(argv[6])==(mock?"--mock-only":"--allow-device-init"),"Explicit mode authorization required");
        out=argv[5];need(!fs::exists(out),"Preserve previous run");fs::create_directory(out);
        const auto started=Clock::now();
        std::array<Payload,2> payloads{load(fs::path(argv[4])/"pattern-0"),load(fs::path(argv[4])/"pattern-1")};
        {
            SdkGroup group(argv[2],argv[3],out,mock);
            if(mock){
                for(size_t p=0;p<2;++p){const auto target=out/("mock-pattern-"+std::to_string(p));fs::create_directory(target);group.memoryRoundTrip(payloads[p],target);}
            }else{
                // Mandatory real memory check uses independent SDK-owned chunks,
                // never the deployed model's input/output storage or NPU.
                for(size_t p=0;p<2;++p){const auto target=out/("memory-pattern-"+std::to_string(p));fs::create_directory(target);group.memoryRoundTrip(payloads[p],target);}
                const auto deployment=text(out/"deployment.json");const auto token=std::to_string(fingerprint(Bytes(deployment.begin(),deployment.end())))+"\n";
                saveText(out/"deployment.ready",token);std::cout<<"DEPLOYMENT_READY\n"<<std::flush;
                // Bounded control gate only. This is never a device fence/delay.
                while(!fs::exists(out/"forward.allow")){
                    need(Clock::now()-started<std::chrono::seconds(295),"Deployment review/control gate timed out");
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                need(text(out/"forward.allow")==token,"Forward gate not bound to this deployment");
                const auto forwardStart=Clock::now();
                for(size_t i=0;i<4;++i){
                    need(Clock::now()-forwardStart<std::chrono::seconds(60),"Four-call overall budget exceeded");
                    const auto target=out/("call-"+std::to_string(i));fs::create_directory(target);
                    const auto& payload=payloads[i%2];
                    saveFile(target/"input-486.f32",payload.inputs[0]);saveFile(target/"input-478.f16",payload.inputs[1]);
                    saveText(target/"identity.json","{\"invocation\":"+std::to_string(i)+",\"pattern\":"+std::to_string(i%2)+"}\n");
                    group.forwardSave(payload,target,i);compareSaved(target,payload);
                    saveText(target/"comparison.json","{\"saved_before_compare\":true,\"FP32_values\":11760,\"bitwise_equal\":true}\n");
                }
                need(Clock::now()-forwardStart<std::chrono::seconds(60),"Four-call overall budget exceeded after final save");
            }
        }
        saveText(out/"summary.json",mock?"{\"status\":\"mock_deployment_and_HostCPTR_passed\",\"NPU_calls\":0,\"mock_PLDDR_roundtrip_supported\":false,\"patterns\":2}\n":"{\"status\":\"independent_four_calls_passed\",\"NPU_calls\":4,\"FP32_values\":47040,\"video\":false}\n");
        std::cout<<(mock?"Mock memory contracts passed; no forward.\n":"Independent A/B/A/B complete, 47040 saved FP32 bitwise.\n");return 0;
    }catch(const std::exception&e){
        if(!out.empty()&&fs::is_directory(out)){try{saveText(out/"failure.txt",e.what());}catch(...){} }
        std::cerr<<"STOP: "<<e.what()<<'\n';return 1;
    }
}
