#include "reference.hpp"
#include "dataset_profile.hpp"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace {
    using namespace pose::events;
    using Timer=std::chrono::steady_clock;
    void need(bool v,const char* message) {if(!v) throw std::runtime_error(message);}
    std::vector<std::string> split(const std::string& line) {
        std::vector<std::string> out;std::stringstream s(line);std::string item;
        while(std::getline(s,item,',')) out.push_back(item);
        return out;
    }
    std::uint64_t integer(const std::string& text) {
        need(!text.empty()&&text.front()!='-'&&text.front()!='+',"Invalid unsigned integer");
        std::size_t n=0;const auto value=std::stoull(text,&n);need(n==text.size(),"Trailing integer data");return value;
    }
    float number(const std::string& text) {
        std::size_t n=0;const auto value=std::stof(text,&n);need(n==text.size(),"Trailing float data");return value;
    }
    double percentile(std::vector<double> values,double fraction) {
        if(values.empty()) return 0;
        std::sort(values.begin(),values.end());
        return values[std::min(values.size()-1,std::size_t(fraction*(values.size()-1)))];
    }
}

int main(int argc,char** argv) {
    try {
        need(argc==4,"Expected: pose_events_offline input.csv new-trace.csv new-summary.json");
        need(!std::filesystem::exists(argv[2])&&!std::filesystem::exists(argv[3]),"Output already exists");
        std::ifstream input(argv[1]);need(bool(input),"Input unavailable");
        std::ofstream trace(argv[2]);need(bool(trace),"Trace unavailable");
        // Confirmed dataset structure is available, but unresolved export/up gates remain closed.
        Processor processor(dataset::archived_config());PlSimulator feedback;
        std::string line;bool header=false,origin=false;
        std::vector<double> processing_us,core_us;std::map<std::string,std::size_t> statuses;
        std::size_t frames=0,events=0,unknown=0,rows=0;Output latest;
        trace<<"kind,now_ns,sequence,stance,trunk,arms,help,reasons,availability,service_alive,input_recent,result_recent,ps_pending,pl_pending,event_epoch,event_id\n";
        const auto start=Timer::now();
        while(std::getline(input,line)) {
            need(line.size()<=16384,"Input row too long");
            if(!line.empty()&&line.back()=='\r') line.pop_back();
            if(line.empty()) continue;
            if(line.front()=='#') {
                if(line=="# origin=archived_board_inference") origin=true;
                continue;
            }
            if(!header) {need(line.rfind("kind,now_ns,epoch,sequence",0)==0,"Unknown CSV schema");header=true;continue;}
            need(origin,"Archive origin declaration required; no semantic verification inferred");
            auto v=split(line);need(v.size()>=4,"Short control row");
            const auto now=integer(v[1]),epoch=integer(v[2]),seq=integer(v[3]);
            const auto before=Timer::now();
            Feedback state;bool state_ready=false;
            if(v[0]=="B") {feedback.begin(now,epoch);processor.break_continuity();}
            else if(v[0]=="H") feedback.heartbeat(now,epoch,seq);
            else if(v[0]=="I") feedback.input(now,epoch,seq);
            else if(v[0]=="T") {}
            else if(v[0]=="S") {feedback.stop(now);processor.break_continuity();latest=processor.latest();}
            else if(v[0]=="X") {feedback.stop(now,true);processor.break_continuity();latest=processor.latest();}
            else if(v[0]=="A") {processor.acknowledge(epoch,seq);feedback.acknowledge(now,epoch,seq);latest=processor.latest();}
            else if(v[0]=="F") {
                need(v.size()==52,"Pose row must contain ten metadata fields and 42 coordinates");
                Frame f;f.now_ns=now;f.epoch=epoch;f.sequence=seq;
                f.capture_ns=integer(v[4]);f.capture_sequence=integer(v[5]);f.segment=v[6];
                // Do not accept timestamps or trust flags invented for archived outputs.
                need(v[7]=="unknown"&&v[8]=="0"&&f.capture_ns==0,"Unverified archive must retain unknown capture time/subject");
                f.origin=Origin::ArchivedInference;f.score=number(v[9]);
                for(std::size_t n=0;n<42;++n) f.coordinates[n]=number(v[10+n]);
                const auto core_begin=Timer::now();
                latest=processor.observe(f);feedback.result(f,latest);state=feedback.tick(now);state_ready=true;
                core_us.push_back(std::chrono::duration<double,std::micro>(Timer::now()-core_begin).count());
                ++frames;
                events+=latest.event_created;unknown+=latest.stance==Stance::Unknown;
            } else throw std::runtime_error("Unknown control kind");
            if(!state_ready) state=feedback.tick(now);
            const double us=std::chrono::duration<double,std::micro>(Timer::now()-before).count();
            if(v[0]=="F") processing_us.push_back(us);
            ++statuses[name(state.availability)];++rows;
            trace<<v[0]<<','<<now<<','<<seq<<','<<name(latest.stance)<<','<<name(latest.trunk)<<','
                 <<name(latest.arms)<<','<<name(latest.help)<<','<<latest.reasons<<','<<name(state.availability)<<','
                 <<state.service_alive<<','<<state.input_recent<<','<<state.result_recent<<','
                 <<latest.request_pending<<','<<state.request_pending<<','<<state.event_epoch<<','<<state.event_id<<'\n';
            need(bool(trace),"Trace write failed");
        }
        need(input.eof()&&header&&frames>0,"Incomplete/empty archive input");
        trace.close();need(bool(trace),"Trace close failed");
        double sum=0,core_sum=0;for(auto x:processing_us) sum+=x;for(auto x:core_us) core_sum+=x;
        std::ofstream summary(argv[3]);summary<<std::setprecision(12);
        summary<<"{\n  \"origin\":\"archived_board_inference\",\n  \"hardware_test\":false,\n"
               <<"  \"dataset_profile\":\""<<dataset::profile<<"\",\n"
               <<"  \"dataset_facts\":{\"joint_count\":"<<dataset::joint_count
               <<",\"training_coordinate_unit\":\""<<dataset::training_coordinate_unit
               <<"\",\"training_preserves_npy_joint_order\":"<<(dataset::training_preserves_npy_joint_order?"true":"false")
               <<",\"nominal_camera_fps_in_paper\":"<<dataset::paper_nominal_capture_fps
               <<",\"capture_timeline_verified\":"<<(dataset::capture_timeline_verified?"true":"false")<<"},\n"
               <<"  \"capture_clock_verified\":false,\n  \"mapping_verified\":false,\n  \"up_verified\":false,\n"
               <<"  \"frames\":"<<frames<<",\n  \"rows\":"<<rows<<",\n  \"unknown_stance\":"<<unknown
               <<",\n  \"help_events\":"<<events<<",\n  \"frame_decode_and_core_us\":{\"mean\":"<<sum/processing_us.size()
               <<",\"p99\":"<<percentile(processing_us,.99)<<",\"max\":"<<*std::max_element(processing_us.begin(),processing_us.end())
               <<"},\n  \"core_and_feedback_us\":{\"mean\":"<<core_sum/core_us.size()<<",\"p99\":"<<percentile(core_us,.99)
               <<",\"max\":"<<*std::max_element(core_us.begin(),core_us.end())
               <<"},\n  \"wall_with_io_ms\":"<<std::chrono::duration<double,std::milli>(Timer::now()-start).count()
               <<",\n  \"processor_size_bytes\":"<<sizeof(Processor)<<",\n  \"feedback_size_bytes\":"<<sizeof(PlSimulator)
               <<",\n  \"availability_rows\":{";
        bool first=true;for(const auto& [k,n]:statuses){if(!first) summary<<',';first=false;summary<<'"'<<k<<"\":"<<n;}
        summary<<"}\n}\n";need(bool(summary),"Summary write failed");
        std::cout<<"ARCHIVE_PROTOTYPE_COMPLETE frames="<<frames<<" unknown="<<unknown<<" help_events="<<events<<'\n';
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
