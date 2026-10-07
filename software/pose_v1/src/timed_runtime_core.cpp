#include "runtime_core.hpp"
#include "runtime_validation.hpp"
#include <atomic>
#include <ctime>
#include "forward_clock.hpp"

namespace pose_v1::runtime {
using namespace runtime_detail;
namespace fc=pose_v1::forward_clock;
namespace { std::atomic<bool> engine_consumed{false}; }
struct Engine::Impl {
    Config config;
    xir::Network graph;
    Device device;
    Session session;
    std::ostringstream trace, execution, readiness;
    std::mutex call_mutex, callback_mutex;
    bool stopped=false, completed=true;
    uint64_t frame=0, invocation=0, next_invocation=0;
    std::set<int64_t> observed;
    size_t zg_count=0;
    double initialization_ms=0;
    Clock::time_point operation_start;int64_t pending_op=-1;
    Tensor caller_input;
    std::vector<char> caller_bytes;
    explicit Impl(const Config& c):config(c) {
        need(c.allow_device_init,"Explicit device initialization authorization required");
        need(!(c.capture && c.minimal_log),"Capture and minimal logging are mutually exclusive");
        bool unused=false;
        need(engine_consumed.compare_exchange_strong(unused,true),"Only one Engine may ever be constructed in this process");
        trace << std::setprecision(17); execution << std::setprecision(17); readiness << std::setprecision(17);
        bridge::configure(c.minimal_log?nullptr:&trace,false);
        const auto begin=Clock::now();
        graph=xir::Network::CreateFromJsonFile(c.graph.string());validate_graph(graph);
        graph.lazyLoadParamsFromFile(c.raw.string());parameters(graph,c.evidence);
        auto host=HostBackend::Init();auto reg=file(c.evidence/"registry.jsonl");
        registry(graph,host,reg,"before");bridge::register_ops(graph,host);registry(graph,host,reg,"after");
        device=open_device(c.evidence);bridge::configure(c.minimal_log?nullptr:&trace,true,device);
        session=Session::Create<zg330::ZG330Backend,HostBackend>(graph.view(),{device,HostDevice::Default()});
        snapshot_bindings(session,graph,c.evidence,"after-create");validate_created_bindings(session,graph);
        session.enableTimeProfile(false);session.apply();
        snapshot_bindings(session,graph,c.evidence,"after-apply");validate_applied_bindings(session,graph,c.evidence);
        initialization_ms=ms(begin);
        if(c.capture)content::configure(c.evidence/"content");
        session.setPreCallBack([this](const Session&,const xir::Operation& op,const Backend&,std::vector<Tensor>&) {
            need(pending_op==-1,"Overlapping operator callbacks; stop timing rather than guess");
            operation_start=Clock::now();pending_op=op->op_id;
        });
        session.setPostCallBack([this](const Session&,const xir::Operation& op,const Backend& backend,std::vector<Tensor>& out) {
            const auto operation_end=Clock::now();
            need(pending_op==op->op_id,"Unpaired operator callbacks");
            fc::record(backend.is<HostBackend>()?"op.host":"op.zg",op->op_id,0,operation_start,operation_end);pending_op=-1;
            std::lock_guard<std::mutex> lock(callback_mutex);
            if(backend.is<HostBackend>())observed.insert(op->op_id);
            if(backend.is<zg330::ZG330Backend>())++zg_count;
            execution << "{\"frame_id\":" << frame << ",\"invocation\":" << invocation << ",\"op_id\":" << op->op_id
                      << ",\"backend\":" << quote(std::string(backend->typeKey()));
            if(!config.minimal_log) {
                execution << ",\"outputs\":[";
                for(size_t i=0;i<out.size();++i){if(i)execution << ',';bridge::tensor_info(execution,out[i]);}
                execution << ']';
            }
            execution << "}\n";
            if(!config.minimal_log)state("post_callback",op->op_id,out);
            if(config.capture && op->op_id==0) {
                need(backend.is<HostBackend>() && out.size()==1 && out[0].dtype()==caller_input.dtype(),"Input0 differs from Host caller contract");
                content::capture(out[0],"input0_output",0,0,&caller_bytes,caller_input);
            }
        });
    }
    void state(const char* where,int64_t opid,const std::vector<Tensor>& tensors) {
        fc::Span sampled("runtime.observation",opid);
        readiness << "{\"frame_id\":" << frame << ",\"invocation\":" << invocation
            << ",\"where\":" << quote(where) << ",\"op_id\":" << opid
            << ",\"layer_count\":" << device.cast<ZG330Device>().layerCount() << ",\"ready\":[";
        for(size_t i=0;i<tensors.size();++i){if(i)readiness << ',';readiness << (tensors[i].isReady()?"true":"false");}
        readiness << "]}\n";
    }
    Result process(const Window& w,const std::string& name,const Tokens& gold) {
        std::unique_lock<std::mutex> guard(call_mutex,std::try_to_lock);
        need(guard.owns_lock(),"Concurrent forward is forbidden");need(!stopped,"Engine is stopped after an exception");
        try {
            Result r;const auto total=Clock::now();const auto cpu_begin=std::clock();
            fc::start(w.frame_id,next_invocation,total);fc::Span whole("runtime.total");
            {fc::Span t("runtime.raw_validation");for(const auto& v:w.csi)need(std::isfinite(v.real()) && std::isfinite(v.imag()),"Non-finite raw CSI");}
            auto begin=Clock::now();r.input=preprocess(w.csi);r.preprocess_ms=ms(begin);fc::record("runtime.preprocess",0,0,begin,Clock::now());
            {fc::Span t("runtime.input_validation");for(float v:r.input)need(std::isfinite(v),"Non-finite PS input");
            need(std::memcmp(r.input.data(),gold.data(),sizeof(Tokens))==0,"PS preprocessing differs from frozen input");}
            r.frame_id=frame=w.frame_id;r.source_time_ns=w.source_time_ns;r.invocation=invocation=next_invocation++;
            observed.clear();zg_count=0;bridge::set_frame(frame,invocation);
            if(config.capture)content::set_context(frame,invocation,name);
            begin=Clock::now();Tensor input(graph.inputs()[0]);input.mallocOn(HostDevice::MemRegion());
            input.write(0,reinterpret_cast<char*>(r.input.data()),sizeof(Tokens));r.prepare_ms=ms(begin);fc::record("runtime.input_prepare",0,0,begin,Clock::now());
            if(config.capture) {
                caller_input=input;caller_bytes.resize(sizeof(Tokens));std::memcpy(caller_bytes.data(),r.input.data(),sizeof(Tokens));
                content::capture(input,"caller_input",0,0,&caller_bytes,caller_input);
            }
            need(completed,"Previous frame is unconfirmed; state clear forbidden");
            r.before_clear=device.cast<ZG330Device>().layerCount();state("before_frame_state_clear",0,{input});
            // The validated r6 per-frame lifecycle: status-only reset, never reset(0).
            begin=Clock::now();device.reset(1);r.before_forward=device.cast<ZG330Device>().layerCount();
            need(r.before_forward==0,"FPGA state clear did not zero layer count");r.state_clear_ms=ms(begin);fc::record("runtime.state_clear",0,0,begin,Clock::now());
            state("before_forward",0,{input});completed=false;
            begin=Clock::now();auto out=session.forward({input});r.forward_ms=ms(begin);fc::record("runtime.forward",0,0,begin,Clock::now());need(pending_op==-1,"Missing post callback");state("after_forward",672,out);
            begin=Clock::now();for(const auto& t:out)need(t.waitForReady(std::chrono::milliseconds(10000)),"Final output wait timed out");
            const auto last=fusion_baseline::sync.at(9191);
            r.completed_layers=device.cast<ZG330Device>().layerCount();
            need(r.completed_layers==uint32_t(last.first+last.second),"Final layer count differs from fixed baseline");
            completed=true;r.final_wait_ms=ms(begin);fc::record("runtime.final_wait",0,0,begin,Clock::now());state("outputs_completed",672,out);
            caller_input=Tensor{};caller_bytes.clear();
            need(out.size()==2 && shape(out[0].dtype(),{1,100}) && shape(out[1].dtype(),{1,100,14,3}),"Runtime output contract differs");
            for(auto id:host_ids)need(observed.count(id)==1,"Missing actual Host execution");
            need(zg_count==7 && observed.size()==7 && observed.count(0)==1,"Actual callback coverage differs");
            r.host_callbacks=observed.size();r.zg_callbacks=zg_count;
            begin=Clock::now();r.scores=dump(out[0],100);r.poses=dump(out[1],4200);r.output_ms=ms(begin);fc::record("runtime.output_read",0,0,begin,Clock::now());state("after_dump",672,out);
            begin=Clock::now();std::array<float,100> scores;std::memcpy(scores.data(),r.scores.data(),r.scores.size());
            r.best_index=std::max_element(scores.begin(),scores.end())-scores.begin();
            std::memcpy(r.selected_pose.data(),r.poses.data()+r.best_index*42*4,42*4);r.selection_ms=ms(begin);fc::record("runtime.selection",0,0,begin,Clock::now());
            r.cpu_ms=1000.0*(std::clock()-cpu_begin)/CLOCKS_PER_SEC;r.process_ms=ms(total);return r;
        } catch(...) { stopped=true;throw; } // No reset/retry/recreate on failure.
    }
    void save() {
        write(config.evidence/"bridge.jsonl",trace.str());write(config.evidence/"operator-execution.jsonl",execution.str());
        write(config.evidence/"readiness.jsonl",readiness.str());
        fc::save(config.evidence/"monotonic-spans.jsonl");
        write(config.evidence/"sdk-profile-setting.json","{\"enabled\":false,\"wall_clock\":\"std::chrono::steady_clock\",\"unit\":\"ns\"}\n");
    }
    ~Impl() { session.setPreCallBack(Session::CallBackFunc{});session.setPostCallBack(Session::CallBackFunc{});bridge::configure(nullptr,false); }
};
Engine::Engine(const Config& c):impl_(std::make_unique<Impl>(c)){}
Engine::~Engine()=default;
Result Engine::process_window(const Window& w,const std::string& n,const Tokens& g){return impl_->process(w,n,g);}
void Engine::save_evidence(){impl_->save();}
double Engine::init_ms()const{return impl_->initialization_ms;}
}
