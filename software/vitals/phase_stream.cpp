#include "stream.hpp"
#include "receiver.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <filesystem>

using namespace pose::vitals;
namespace {
std::string quoted(const std::string& s){std::ostringstream o;o<<'"';for(unsigned char c:s){if(c=='"'||c=='\\')o<<'\\'<<c;else if(c>=32&&c<127)o<<c;else{o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;}}o<<'"';return o.str();}
void emit(std::ostream& o,const StreamUpdate& u,const std::string& origin){
    o<<std::setprecision(12)<<"{\"schema\":\"PIWVITAL1\",\"version\":1,\"origin\":"<<quoted(origin)
     <<",\"session\":"<<u.session<<",\"sequence\":"<<u.sequence<<",\"first_ns\":"<<u.first_ns<<",\"last_ns\":"<<u.last_ns
     <<",\"buffered\":"<<u.buffered<<",\"resets\":"<<u.resets<<",\"status\":"<<quoted(u.result.status)
     <<",\"backend\":"<<quoted(u.result.correlation_backend)<<",\"heart_bpm\":";
    if(u.result.heart)o<<u.result.heart->bpm;else o<<"null";
    o<<",\"breath_per_minute\":";if(u.result.breath)o<<u.result.breath->bpm;else o<<"null";
    o<<",\"confidence\":";if(u.result.heart)o<<u.result.heart->confidence;else o<<"null";
    o<<",\"total_ms\":"<<u.result.timing.total_ms<<",\"reasons\":[";
    for(std::size_t i=0;i<u.result.reasons.size();++i){if(i)o<<',';o<<quoted(u.result.reasons[i]);}
    o<<"],\"channels\":[";
    for(std::size_t ch=0;ch<channels;++ch){if(ch)o<<',';const auto& h=u.result.trace[ch].heart_candidate;
        o<<"{\"usable\":"<<(h.usable?"true":"false")<<",\"reason\":"<<quoted(h.reason)
         <<",\"acf_hz\":"<<h.acf_hz<<",\"spectral_hz\":"<<h.spectral_hz<<",\"correlation\":"<<h.correlation
         <<",\"concentration\":"<<h.concentration<<",\"energy_ratio\":"<<h.energy_ratio<<'}';}
    o<<"]}\n";
}
}
int main(int argc,char**argv){try{
    std::string input,output,backend="cpu";
    for(int i=1;i<argc;i+=2){if(i+1>=argc)throw std::runtime_error("Missing argument value");std::string key=argv[i];
        if(key=="--input")input=argv[i+1];else if(key=="--output")output=argv[i+1];else if(key=="--backend")backend=argv[i+1];else throw std::runtime_error("Unknown argument");}
    if(input.empty()||output.empty()||(backend!="cpu"&&backend!="fixed-reference"))throw std::runtime_error("Use --input derived-phase.csv --output new.jsonl [--backend cpu|fixed-reference]");
    if(output!="-"&&std::filesystem::exists(output))throw std::runtime_error("Output already exists");
    std::ifstream file;if(input!="-")file.open(input);std::istream& in=input=="-"?std::cin:file;if(!in)throw std::runtime_error("Cannot open input");
    std::string line,origin,clock,evidence;bool header=false,raw=false,first_line=true;std::size_t bytes=0;
    std::string raw_header="session,time_ns,sequence,valid";for(unsigned c=0;c<4;++c)for(const char* part:{"ia","qa","ib","qb"})raw_header+=","+std::string(part)+std::to_string(c);
    while(std::getline(in,line)){bytes+=line.size()+1;if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(first_line&&line.rfind("\xef\xbb\xbf",0)==0)line.erase(0,3);first_line=false;
        if(line.rfind("# origin=",0)==0){if(!origin.empty())throw std::runtime_error("Duplicate origin");origin=line.substr(9);}
        else if(line.rfind("# clock=",0)==0){if(!clock.empty())throw std::runtime_error("Duplicate clock");clock=line.substr(8);}
        else if(line.rfind("# clock_evidence=",0)==0){if(!evidence.empty())throw std::runtime_error("Duplicate provenance");evidence=line.substr(17);}
        else if(line=="session,time_ns,sequence,source_support_valid,p0,p1,p2,p3"){header=true;break;}
        else if(line==raw_header){header=true;raw=true;break;}
        else if(!line.empty())throw std::runtime_error("Invalid phase header");
        if(bytes>8192)throw std::runtime_error("Phase header too long");
    }
    PhaseClock kind=PhaseClock::Unknown;
    if(origin=="synthetic"&&clock=="synthetic_uniform")kind=PhaseClock::Synthetic;
    if(origin=="real_capture"&&clock==(raw?"relative_rx":"derived_relative_rx"))kind=PhaseClock::RelativeRx;
    if(!header||kind==PhaseClock::Unknown||evidence.empty())throw std::runtime_error("Unknown/conflicting phase provenance");
    ScalarDots scalar;FixedCorrelation fixed(scalar);auto selected_backend=backend=="cpu"?nullptr:&fixed;
    PhaseStream stream(kind,evidence,{},selected_backend);ReceiverStream receiver(kind,evidence,selected_backend);
    std::ofstream output_file;if(output!="-")output_file.open(output);std::ostream& out=output=="-"?std::cout:output_file;if(!out)throw std::runtime_error("Cannot open output");
    std::uint64_t rows=0,estimates=0,last_emitted_ns=0;StreamUpdate last;std::string previous_status;
    while(std::getline(in,line)){bytes+=line.size()+1;if(bytes>16*1024*1024||++rows>50000||line.size()>1024)throw std::runtime_error("Phase file budget exceeded");
        if(!line.empty()&&line.back()=='\r')line.pop_back();std::stringstream row(line);std::string field;std::vector<std::string> fields;
        while(std::getline(row,field,','))fields.push_back(field);if(fields.size()!=(raw?20u:8u))throw std::runtime_error("Input row width");
        auto integer=[](const std::string& s){if(s.empty()||s.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("Invalid unsigned integer");return std::stoull(s);};
        auto real=[](const std::string& s){std::size_t used=0;const auto v=std::stod(s,&used);if(used!=s.size())throw std::runtime_error("Invalid phase numeric field");return v;};
        const auto session=integer(fields[0]),stamp=integer(fields[1]),sequence=integer(fields[2]);
        if(fields[3]!="0"&&fields[3]!="1")throw std::runtime_error("Invalid support flag");const bool valid=fields[3]=="1";
        std::vector<StreamUpdate> updates;
        if(raw){ReceiverSample sample;sample.session=session;sample.time_ns=stamp;sample.event_sequence=sequence;sample.valid=valid;
            for(std::size_t c=0;c<channels;++c)sample.pairs[c]={{real(fields[4+c*4]),real(fields[5+c*4])},{real(fields[6+c*4]),real(fields[7+c*4])}};
            updates=receiver.push(sample);
        }else{PhaseSample sample;sample.time_ns=stamp;sample.sequence=sequence;sample.source_support_valid=valid;
            for(std::size_t c=0;c<channels;++c)sample.phase[c]=real(fields[c+4]);updates.push_back(stream.push(session,sample));}
        for(auto& update:updates){last=std::move(update);const auto& status=last.result.status;
            const bool analysis=status!="warming_up"&&status!="waiting_next_analysis"&&status!="invalid";
            if(previous_status.empty()||analysis||(status=="invalid"&&previous_status!="invalid")||last.last_ns<last_emitted_ns||last.last_ns-last_emitted_ns>=1000000000){
                emit(out,last,origin);out.flush();last_emitted_ns=last.last_ns;previous_status=status;if(last.result.heart)++estimates;
            }
        }
    }
    if(!rows)throw std::runtime_error("Empty phase input");
    // EOF is loss of source availability, not a last valid estimate to display indefinitely.
    last=raw?receiver.invalidate("source_ended"):stream.invalidate("source_ended");
    last.result.status="source_ended";emit(out,last,origin);
    out.flush();if(!out)throw std::runtime_error("Output write failure");
    std::cerr<<"rows="<<rows<<" estimates="<<estimates<<"\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
