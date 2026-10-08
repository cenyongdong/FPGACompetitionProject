#include "failed_result_evidence.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>

int main(int argc,char**argv){try{
    if(argc!=2||std::filesystem::exists(argv[1]))throw std::runtime_error("Fresh selftest path required");
    const std::filesystem::path root=argv[1];std::filesystem::create_directory(root);
    pose::validation::FixtureWindow c{};c.name="capture-contract";c.window.frame_id=7;
    pose_v1::application::Result r{};r.frame_id=7;r.host_callbacks=r.zg_callbacks=7;r.completed_layers=745;
    for(unsigned i=0;i<3;++i){
        const auto out=root/std::to_string(i);std::filesystem::create_directory(out);std::ofstream log(out/"calls.jsonl");
        if(i==1){r.scores[0]=.125f;r.poses[2]=-.5f;}
        if(i==2)r.scores[0]=std::numeric_limits<float>::quiet_NaN();
        bool rejected=false;
        try{pose::validation::saveOrCaptureFailedResult(c,r,c.window,0,out,log);}
        catch(const std::exception& e){rejected=true;if(std::string(e.what())!="Actual model outputs differ")throw;}
        if(rejected!=(i!=0)||std::filesystem::exists(out/"failed-result")!=(i!=0))throw std::runtime_error("Capture changed original gate outcome");
        if(i&&std::filesystem::file_size(out/"failed-result/scores.f32")!=400)throw std::runtime_error("Rejected bytes not preserved");
    }
    std::cout<<"{\"status\":\"passed\",\"positive\":1,\"failure_preserved\":2,\"original_exception\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
