#include "h264_access_unit.hpp"
#include <stdexcept>

namespace pose::stream {
namespace {
void check(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
size_t prefix(const Bytes& b,size_t i){
    if(i+3<=b.size()&&b[i]==0&&b[i+1]==0&&b[i+2]==1)return 3;
    if(i+4<=b.size()&&b[i]==0&&b[i+1]==0&&b[i+2]==0&&b[i+3]==1)return 4;
    return 0;
}
}
std::optional<AccessUnit> AccessUnitAssembler::consume(const Bytes& bytes,int64_t pts){
    check(pts>=0&&bytes.size()<=262144,"Capture PTS/capacity invalid");
    if(bytes.empty())return {};
    // Validate the whole capture before committing any parser state.
    Bytes sps=sps_,pps=pps_,slice;bool idr=false;size_t offset=0;
    while(offset<bytes.size()){
        size_t start=prefix(bytes,offset);check(start!=0,"Incomplete Annex B prefix");
        size_t end=offset+start;while(end<bytes.size()&&!prefix(bytes,end))++end;
        check(end>offset+start,"Empty NAL");Bytes nal(bytes.begin()+offset+start,bytes.begin()+end);
        check(!(nal[0]&0x80),"Forbidden NAL bit");unsigned type=nal[0]&31;
        if(type==7||type==8){
            check(slice.empty()&&nal.size()>=4&&nal.size()<=4096,"Parameter layout/capacity invalid");
            auto& stored=type==7?sps:pps;check(stored.empty()||stored==nal,"Parameter set changed");stored=std::move(nal);
        }else{
            check(type==1||type==5,"Unsupported NAL type");
            check(slice.empty()&&nal.size()>1&&(nal[1]&0x80),"Unsupported multi-slice picture");
            check(!sps.empty()&&!pps.empty(),"VCL before parameters");
            check(count_>0||type==5,"First picture must be IDR");
            check(pts>lastPts_,"Picture PTS did not increase");slice=std::move(nal);idr=type==5;
        }
        offset=end;
    }
    if(slice.empty()){sps_=std::move(sps);pps_=std::move(pps);return {};}
    AccessUnit unit{count_,pts,sps,pps,std::move(slice),idr};
    sps_=std::move(sps);pps_=std::move(pps);lastPts_=pts;++count_;return unit;
}
}
