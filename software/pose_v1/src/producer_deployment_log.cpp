// Public SDK deployment log only. Frozen registration/validation reused.
#pragma GCC diagnostic push
// Frozen validation header has the already-recorded open_device formatting
// warning. Keep its bytes; retain Werror for the new entry after this include.
#pragma GCC diagnostic ignored "-Wmisleading-indentation"
#include "lazy_runtime_validation.hpp"
#pragma GCC diagnostic pop
#include <iostream>
int main(int argc,char**argv){
    using namespace pose_v1::runtime_detail;
    fs::path out;
    try{
        need(argc==5&&std::string(argv[4])=="--allow-device-init","GRAPH RAW FRESH-OUTPUT --allow-device-init required");
        out=argv[3];need(!fs::exists(out),"Preserve prior deployment evidence");fs::create_directory(out);
        auto graph=xir::Network::CreateFromJsonFile(argv[1]);validate_graph(graph);graph.lazyLoadParamsFromFile(argv[2]);parameters(graph,out);
        need(graph->name=="piw24","Pinned model name differs");
        const fs::path logdir=fs::path(".icraft")/"logs"/"piw24";
        need(!fs::exists(".icraft"),"Fresh official log work directory required");
        // Host-only contract: SDK stream cannot open a missing nested parent.
        bool missing_open=false;{icraft::midware::ofstream f((logdir/"stream-contract.txt").string());missing_open=f.is_open();}
        need(!missing_open,"Unexpected SDK parent creation behavior; stop");
        fs::create_directories(logdir);
        {icraft::midware::ofstream f((logdir/"stream-contract.txt").string());need(f.is_open(),"SDK stream parent preparation failed");f<<"owned-log-parent-contract\n";f.close();}
        file(out/"log-parent-contract.json")<<"{\"missing_parent_opened\":false,\"prepared_parent_opened\":true,\"Device_opened_during_contract\":false}\n";
        auto host=HostBackend::Init();auto regs=file(out/"registry.jsonl");registry(graph,host,regs,"before");bridge::register_ops(graph,host);registry(graph,host,regs,"after");
        auto device=open_device(out);
        {
            auto session=Session::Create<zg330::ZG330Backend,HostBackend>(graph.view(),{device,HostDevice::Default()});
            snapshot_bindings(session,graph,out,"after-create");validate_created_bindings(session,graph);
            session.enableTimeProfile(false);session.apply();snapshot_bindings(session,graph,out,"after-apply");validate_applied_bindings(session,graph,out);
            // The documented log() API writes deployment maps; no forward,
            // tensor/device data read, private map access or cache operation.
            const auto bindings=session.backendBindings();std::set<uintptr_t> seen;size_t logged=0;
            for(const auto&entry:bindings){const auto&backend=entry.second;
                if(backend.is<zg330::ZG330Backend>()&&seen.insert(reinterpret_cast<uintptr_t>(backend.operator->())).second){backend.cast<zg330::ZG330Backend>().log();++logged;}
            }
            need(logged==1,"Expected exactly one deployed ZG backend");
            size_t logfiles=0;for(const auto&p:fs::directory_iterator(logdir)){if(p.is_regular_file()&&p.path().extension()==".log"){need(p.file_size()>0,"Empty official SDK log");++logfiles;}}
            // SDK3.39 emits a deployment log plus its memory optimization log.
            need(logfiles==2,"Official SDK log pair missing/ambiguous; stop");
            file(out/"summary.json")<<"{\"status\":\"official_deployment_log_saved\",\"full_model_forward\":false,\"extra_device_data_reads\":0,\"log_calls\":1,\"SDK_profiling\":false,\"actual_log_files\":2}\n";
        }
        std::cout<<"Official deployment log saved; no forward/VPU/TCP.\n";return 0;
    }catch(const std::exception&e){
        if(!out.empty()&&fs::is_directory(out)){try{file(out/"failure.txt")<<e.what()<<'\n';}catch(...){} }
        std::cerr<<"STOP: "<<e.what()<<'\n';return 1;
    }
}
