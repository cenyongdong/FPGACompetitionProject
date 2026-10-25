#include "reference.hpp"
#include "dataset_profile.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

using namespace pose::events;
namespace {
    int cases=0;
    void check(bool v,const char* m) {if(!v) throw std::runtime_error(m);}
    template<class F> void rejects(F f) {bool caught=false;try{f();}catch(const std::invalid_argument&){caught=true;}check(caught,"Expected contract rejection");}
    template<class F> void test(const char* n,F f) {f();++cases;std::cout<<"PASS "<<n<<'\n';}
    Config analytic() {
        Config c;c.contract.mapping_verified=c.contract.up_verified=true;
        c.contract.mapping_evidence="Analytic fixture only; NOT a Person-in-WiFi index mapping";
        c.contract.up_evidence="Analytic Cartesian z-up fixture only";
        c.contract.up={0,0,1};c.contract.joints={0,1,2,3,4,5,6,7,8,9,10,11};return c;
    }
    Frame frame(std::uint64_t index,bool raised=false,bool sit=false,bool bend=false) {
        Frame f;f.sequence=f.capture_sequence=index;f.now_ns=f.capture_ns=1000000000+index*50000000;
        f.epoch=1;f.segment="analytic";f.origin=Origin::Synthetic;f.clock=Clock::Synthetic;
        f.subject_verified=true;f.score=1;
        auto p=[&](int i,double x,double y,double z){f.coordinates[3*i]=float(x);f.coordinates[3*i+1]=float(y);f.coordinates[3*i+2]=float(z);};
        const double hip=sit?.5:1,sy=bend?.6:0,sz=hip+(bend?.3:.5);
        p(0,-.2,sy,sz);p(1,.2,sy,sz);p(2,-.15,0,hip);p(3,.15,0,hip);
        p(4,-.15,sit?.45:0,.5);p(5,.15,sit?.45:0,.5);
        p(6,-.15,sit?.45:0,0);p(7,.15,sit?.45:0,0);
        p(8,-.25,sy,sz+(raised?.2:-.25));p(9,.25,sy,sz-.25);
        p(10,-.25,sy,sz+(raised?.5:-.5));p(11,.25,sy,sz-.5);
        p(12,0,sy,sz+.2);p(13,0,sy,sz);return f;
    }
    Output feed(Processor& p,std::uint64_t first,std::uint64_t last,bool raised=false,bool sit=false,bool bend=false) {
        Output out;for(auto i=first;i<=last;++i)out=p.observe(frame(i,raised,sit,bend));return out;
    }
    struct Metric {double mean=0,p99=0,max=0;std::size_t n=0;};
    Metric benchmark(bool verified) {
        Processor p(verified?analytic():Config{});PlSimulator sim;sim.begin(0,1);
        std::vector<double> times;times.reserve(50000);double sum=0;
        for(std::uint64_t i=1;i<=50000;++i) {
            auto f=frame(i,(i/100)%2,(i/200)%2,(i/300)%2);
            if(!verified) {f.origin=Origin::ArchivedInference;f.clock=Clock::Unknown;f.capture_ns=0;f.subject_verified=false;}
            const auto t=std::chrono::steady_clock::now();
            sim.heartbeat(f.now_ns,1,i);sim.input(f.now_ns,1,i);
            auto out=p.observe(f);sim.result(f,out);auto feedback=sim.tick(f.now_ns);
            const auto us=std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-t).count();
            check(feedback.availability!=(verified?Availability::Unverified:Availability::Available),"Benchmark mode confused");
            if(out.request_pending && i%100==0) {p.acknowledge(out.event_epoch,out.event_id);sim.acknowledge(f.now_ns,out.event_epoch,out.event_id);}
            times.push_back(us);sum+=us;
        }
        std::sort(times.begin(),times.end());return {sum/times.size(),times[49499],times.back(),times.size()};
    }
}
int main(int argc,char** argv) {
    try {
        check(argc==1||argc==3,"Optional arguments: new-summary.json new-feedback-trace.csv");
        if(argc==3) check(!std::filesystem::exists(argv[1])&&!std::filesystem::exists(argv[2]),"Output exists");
        test("mapping/up evidence, distinct indices, valid thresholds",[]{
            auto c=analytic();c.contract.mapping_evidence.clear();rejects([&]{Processor p(c);});
            c=analytic();c.contract.joints.wrist_l=c.contract.joints.shoulder_l;rejects([&]{Processor p(c);});
            c=analytic();c.contract.up={0,0,0};rejects([&]{Processor p(c);});
            c=analytic();c.hold_ns=0;rejects([&]{Processor p(c);});
            c=analytic();c.score_min=std::numeric_limits<double>::quiet_NaN();rejects([&]{Processor p(c);});
        });
        test("unknown archive remains unknown and input bytes untouched",[]{
            Processor p;auto f=frame(1);f.clock=Clock::Unknown;f.capture_ns=0;f.subject_verified=false;f.origin=Origin::ArchivedInference;
            const auto saved=f.coordinates;auto o=p.observe(f);
            check(o.stance==Stance::Unknown&&o.help==Help::Unknown&&!o.event_created,"Archive invented an action");
            check((o.reasons&(MappingUnknown|UpUnknown|TimeUnknown|SubjectUnknown))==15,"Missing unknown causes");
            check(std::memcmp(saved.data(),f.coordinates.data(),sizeof(saved))==0,"Raw pose changed");
        });
        test("audited dataset facts cannot enable unverified semantic mapping",[]{
            check(dataset::joint_count==14&&dataset::training_preserves_npy_joint_order,"Dataset structure lost");
            auto c=dataset::archived_config();
            // Even a plausible paper/topology index assignment cannot supply missing evidence.
            c.contract.joints={2,3,5,7,9,11,12,13,4,6,8,10};
            Processor p(c);auto f=frame(1);f.origin=Origin::ArchivedInference;f.clock=Clock::VerifiedCapture;
            const auto o=p.observe(f);
            check((o.reasons&(MappingUnknown|UpUnknown))==(MappingUnknown|UpUnknown),"Candidate map promoted");
            check(!o.features_valid&&!o.event_created&&o.help==Help::Unknown,"Audit invented a semantic action");
        });
        test("nominal dataset FPS and raw suffix cannot establish capture time",[]{
            check(dataset::paper_nominal_capture_fps==15&&!dataset::capture_timeline_verified,"Nominal FPS promoted");
            Processor p(dataset::archived_config());auto f=frame(1);
            f.origin=Origin::ArchivedInference;f.clock=Clock::Unknown;f.capture_ns=0;f.subject_verified=false;
            const auto o=p.observe(f);
            check((o.reasons&(TimeUnknown|SubjectUnknown))==(TimeUnknown|SubjectUnknown),"Missing timeline accepted");
        });
        test("standing upright confirmed only after 300ms",[]{Processor p(analytic());check(feed(p,1,6).stance==Stance::Unknown,"Too early");auto o=feed(p,7,8);check(o.stance==Stance::Standing&&o.trunk==Trunk::Upright,"Stand failed");});
        test("sitting and raised arm remain orthogonal",[]{Processor p(analytic());auto o=feed(p,1,10,true,true);check(o.stance==Stance::Sitting&&o.arms==Arms::Raised,"Sit/raise conflict");});
        test("bending detected independently from standing",[]{Processor p(analytic());auto o=feed(p,1,10,false,false,true);check(o.stance==Stance::Standing&&o.trunk==Trunk::Leaning,"Bend failed");});
        test("brief raise cannot request assistance",[]{Processor p(analytic());check(!feed(p,1,16,true).request_pending,"Short hold requested help");check(!feed(p,17,30).request_pending,"Release created help");});
        test("alternating arms cannot borrow each other's hold duration",[]{
            Processor p(analytic());
            for(std::uint64_t i=1;i<=50;++i){auto f=frame(i,true);
                if(i%2){f.coordinates[3*8+2]=1.25f;f.coordinates[3*10+2]=1.0f;f.coordinates[3*9+2]=1.7f;f.coordinates[3*11+2]=2.0f;}
                check(!p.observe(f).request_pending,"Different arms accumulated a one-second hold");}
        });
        test("same raised arm survives a temporary second raised arm",[]{
            Processor p(analytic());Output o;
            for(std::uint64_t i=1;i<=21;++i){auto f=frame(i,true);if(i>=5&&i<=10){f.coordinates[3*9+2]=1.7f;f.coordinates[3*11+2]=2.0f;}o=p.observe(f);}
            check(o.event_created,"Continuous left arm lost hold duration");
        });
        test("one second creates exactly one latched event",[]{Processor p(analytic());auto o=feed(p,1,20,true);check(!o.request_pending,"Hold too early");o=feed(p,21,21,true);check(o.event_created&&o.event_id==1,"No event at 1s");o=feed(p,22,80,true);check(o.request_pending&&!o.event_created&&o.event_id==1,"Repeated event");});
        test("lowering arm, missing data and continuity breaks preserve request",[]{
            Processor p(analytic());feed(p,1,21,true);auto o=feed(p,22,35);check(o.request_pending,"Lowering cleared request");
            auto f=frame(36);f.subject_verified=false;o=p.observe(f);check(o.request_pending&&o.help==Help::Latched,"Invalid frame cleared request");p.break_continuity();check(p.latest().request_pending&&!p.latest().features_valid,"Break cleared request/kept valid pose");
        });
        test("acknowledgment IDs and release-to-rearm",[]{
            Processor p(analytic());feed(p,1,21,true);check(!p.acknowledge(1,9)&&!p.acknowledge(2,1)&&p.acknowledge(1,1),"Ack IDs/epoch failed");
            check(!feed(p,22,50,true).request_pending,"Raised arm retriggered after ack");
            feed(p,51,61);check(feed(p,62,82,true).event_id==2&&p.latest().event_created,"Rearm failed");
        });
        for(int mode=0;mode<6;++mode) test(("continuity boundary "+std::to_string(mode)).c_str(),[mode]{
            Processor p(analytic());feed(p,1,16,true);auto f=frame(17,true);
            if(mode==0)f.segment="other";
            if(mode==1)f.capture_sequence+=3;
            if(mode==2)f.capture_ns-=300000000;
            if(mode==3)f.capture_ns+=500000000;
            if(mode==4)f.epoch=2;
            if(mode==5)f.clock=Clock::Unknown;
            auto o=p.observe(f);check(!o.request_pending,"Boundary retained hold duration");
            check(o.stance==Stance::Unknown,"Boundary retained confirmed stance");
        });
        test("duplicate sequences cannot accumulate hold",[]{Processor p(analytic());auto f=frame(1,true);p.observe(f);for(int i=0;i<40;++i){f.now_ns+=50000000;f.capture_ns+=50000000;auto o=p.observe(f);check((o.reasons&Duplicate)&&!o.request_pending,"Duplicate generated help");}});
        test("NaN, low score and unverified subject refuse action",[]{
            for(int n=0;n<3;++n){Processor p(analytic());feed(p,1,16,true);auto f=frame(17,true);
                if(n==0) f.coordinates[0]=std::numeric_limits<float>::quiet_NaN();
                if(n==1) f.score=.49f;
                if(n==2) f.subject_verified=false;
                auto o=p.observe(f);check(!o.features_valid&&!o.request_pending&&o.arms==Arms::Unknown,"Invalid action accepted");}
        });
        test("synthetic clock cannot validate archived output",[]{Processor p(analytic());auto f=frame(1,true);f.origin=Origin::ArchivedInference;check(p.observe(f).reasons&TimeUnknown,"Archive clock invented");});
        test("zero identity refused",[]{Processor p(analytic());auto f=frame(1);f.sequence=0;check(p.observe(f).reasons&IdentityUnknown,"Zero ID accepted");});
        test("degenerate geometry refuses action",[]{Processor p(analytic());auto f=frame(1);f.coordinates.fill(0);check(p.observe(f).reasons&Degenerate,"Zero geometry accepted");});
        test("stale service exact boundary",[]{PlSimulator s;s.begin(0,1);s.heartbeat(0,1,1);check(s.tick(499999999).service_alive,"Heartbeat expired early");check(s.tick(500000000).availability==Availability::ServiceLost,"Heartbeat timeout failed");});
        test("startup cannot show available before first heartbeat",[]{
            PlSimulator s;s.begin(0,1);Processor p(analytic());auto f=frame(1);f.now_ns=100000000;
            s.input(f.now_ns,1,1);s.result(f,p.observe(f));check(s.tick(f.now_ns).availability==Availability::Initializing,"Startup bypassed heartbeat");
        });
        test("duplicate heartbeat cannot renew lease",[]{PlSimulator s;s.begin(0,1);s.heartbeat(0,1,1);check(!s.heartbeat(450000000,1,1),"Duplicate accepted");check(s.tick(500000000).availability==Availability::ServiceLost,"Lease renewed by duplicate");});
        test("input freshness and result freshness are independent",[]{
            Processor p(analytic());PlSimulator s;s.begin(0,1);auto f=frame(1);auto o=p.observe(f);
            s.heartbeat(f.now_ns,1,1);s.input(f.now_ns,1,1);s.result(f,o);
            auto now=f.now_ns+300000000;s.heartbeat(now,1,2);s.input(now,1,2);
            check(s.tick(now).availability==Availability::ResultStale,"Fresh input masked stale result");
        });
        test("new result cannot mask stale input",[]{
            Processor p(analytic());PlSimulator s;s.begin(0,1);auto f=frame(1);s.heartbeat(f.now_ns,1,1);s.input(f.now_ns,1,1);s.result(f,p.observe(f));
            f=frame(8);s.heartbeat(f.now_ns,1,2);s.result(f,p.observe(f));check(s.tick(f.now_ns).availability==Availability::InputStale,"Result masked stale input");
        });
        test("duplicate result does not refresh progress",[]{
            Processor p(analytic());PlSimulator s;s.begin(0,1);auto f=frame(1);auto o=p.observe(f);s.heartbeat(f.now_ns,1,1);s.input(f.now_ns,1,1);s.result(f,o);
            f.now_ns+=300000000;s.heartbeat(f.now_ns,1,2);s.input(f.now_ns,1,2);check(!s.result(f,o),"Duplicate result accepted");check(s.tick(f.now_ns).availability==Availability::ResultStale,"Duplicate refreshed result");
        });
        test("old epoch and same-epoch restart refused",[]{PlSimulator s;s.begin(0,2);check(!s.heartbeat(1,1,1),"Old epoch accepted");rejects([&]{s.begin(2,2);});});
        test("unknown archives never show available",[]{Processor p;PlSimulator s;s.begin(0,1);auto f=frame(1);f.origin=Origin::ArchivedInference;s.heartbeat(f.now_ns,1,1);s.input(f.now_ns,1,1);s.result(f,p.observe(f));check(s.tick(f.now_ns).availability==Availability::Unverified,"Archive labeled available");});
        test("virtual clock regression refused",[]{PlSimulator s;s.begin(10,1);rejects([&]{s.tick(9);});});
        std::vector<std::string> feedback_trace;
        test("PS freeze preserves request in PL simulation",[&]{
            Processor p(analytic());PlSimulator s;s.begin(0,1);Frame f;Output o;
            for(int i=1;i<=21;++i){f=frame(i,true);o=p.observe(f);s.heartbeat(f.now_ns,1,i);s.input(f.now_ns,1,i);s.result(f,o);}
            auto log=[&](Ns now){auto v=s.tick(now);feedback_trace.push_back(std::to_string(now)+","+name(v.availability)+","+std::to_string(v.request_pending)+","+std::to_string(v.event_id));return v;};
            check(log(f.now_ns).request_pending,"No pending PL request");
            check(log(f.now_ns+500000000).availability==Availability::ServiceLost,"PS freeze not detected");
            check(!s.acknowledge(f.now_ns+500000001,1,99),"Wrong ack cleared latch");
            s.stop(f.now_ns+500000002,true);check(log(f.now_ns+500000002).request_pending,"Fault cleared latch");
            s.begin(f.now_ns+500000003,2);check(log(f.now_ns+500000003).request_pending,"Epoch change cleared latch");
            check(!s.acknowledge(f.now_ns+500000004,2,1),"New epoch ack cleared old event");
            check(s.acknowledge(f.now_ns+500000004,1,1)&&!log(f.now_ns+500000004).request_pending,"Correct ack failed");
        });
        test("new-epoch event IDs do not overwrite pending older requests",[]{
            Processor a(analytic());PlSimulator s;s.begin(0,1);Frame f;Output out;
            for(int i=1;i<=21;++i){f=frame(i,true);out=a.observe(f);s.heartbeat(f.now_ns,1,i);s.input(f.now_ns,1,i);s.result(f,out);}
            s.begin(f.now_ns+1,2);Processor b(analytic());
            for(int i=1;i<=21;++i){auto next=frame(i,true);next.epoch=2;next.now_ns+=2000000000;next.capture_ns+=2000000000;auto o=b.observe(next);s.heartbeat(next.now_ns,2,i);s.input(next.now_ns,2,i);s.result(next,o);f=next;}
            auto state=s.tick(f.now_ns);check(state.event_epoch==1&&state.event_id==1&&state.request_pending,"Pending event overwritten");
            check(!s.acknowledge(f.now_ns,2,1)&&s.acknowledge(f.now_ns,1,1),"Epoch latch ACK confused");
            f=frame(22,true);f.epoch=2;f.now_ns+=2000000000;f.capture_ns+=2000000000;
            s.heartbeat(f.now_ns,2,22);s.input(f.now_ns,2,22);s.result(f,b.observe(f));
            state=s.tick(f.now_ns);check(state.event_epoch==2&&state.request_pending,"New epoch pending request lost after old ACK");
        });
        test("stop does not become healthy through heartbeat",[]{PlSimulator s;s.begin(0,1);s.stop(1);check(!s.heartbeat(2,1,1)&&s.tick(2).availability==Availability::Stopped,"Stopped became healthy");});
        const auto valid=benchmark(true),unknown=benchmark(false);
        auto emit=[&](std::ostream& s){
            auto metric=[&](const Metric& m){s<<"{\"n\":"<<m.n<<",\"mean\":"<<m.mean<<",\"p99\":"<<m.p99<<",\"max\":"<<m.max<<'}';};
            s<<std::setprecision(12)<<"{\"passed_cases\":"<<cases<<",\"synthetic_logic_only\":true,\"hardware_test\":false,\"host_core_and_feedback_us\":{\"verified_synthetic\":";
            metric(valid);s<<",\"unverified_archive_branch\":";metric(unknown);
            s<<"},\"processor_size_bytes\":"<<sizeof(Processor)<<",\"feedback_size_bytes\":"<<sizeof(PlSimulator)<<"}\n";
        };
        if(argc==3){std::ofstream out(argv[1]);emit(out);check(bool(out),"Summary write failed");std::ofstream trace(argv[2]);trace<<"now_ns,availability,request_pending,event_id\n";for(const auto& row:feedback_trace)trace<<row<<'\n';check(bool(trace),"Trace write failed");}
        emit(std::cout);return 0;
    } catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}
