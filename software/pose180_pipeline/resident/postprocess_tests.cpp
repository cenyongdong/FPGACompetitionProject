#include "postprocess.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
using namespace pose::post;
static void check(bool p,const char*s){if(!p)throw std::runtime_error(s);}
struct Sample {
 std::array<float,180> scores{};std::array<float,7560> poses{};std::uint64_t ns=1000000000,seq=1,session=1;
 void person(unsigned i,double x,float score=.8f){scores[i]=score;for(unsigned j=0;j<14;++j){poses[i*42+j*3]=float(x+.05*(int(j%3)-1));poses[i*42+j*3+1]=float(.1*(int(j%2)-1));poses[i*42+j*3+2]=float(.15*j);}}
 PresentationFrame run(Postprocessor&p){return p.update({session,seq,seq,ns},scores.data(),poses.data());}
 void next(unsigned ms=67){ns+=std::uint64_t(ms)*1000000;++seq;}
};
int main(){try{
 Postprocessor p;Sample s;s.person(7,1);check(s.run(p).poses.empty(),"birth confirmation");s.next();auto f=s.run(p);check(f.poses.size()==1,"second confirmation");auto id=f.poses[0].track;
 s.scores[7]=0;s.person(19,1.01);s.next();f=s.run(p);check(f.poses[0].track==id&&f.poses[0].candidate==19,"query is not identity");
 s.person(20,1.01,.79f);s.next();f=s.run(p);check(f.poses.size()==1&&p.metrics().duplicates>0,"dedup");
 s.scores.fill(.2f);s.next();f=s.run(p);check(f.poses.size()==1&&f.poses[0].held,"strict threshold/hold");s.next(251);check(s.run(p).poses.empty(),"expiry");
 s.person(1,1);s.next();check(s.run(p).poses.empty(),"reappearance first");s.next();f=s.run(p);check(f.poses.size()==1&&f.poses[0].track!=id,"new identity after expiry");id=f.poses[0].track;
 s.person(1,10);s.next();f=s.run(p);check(f.poses.size()==1&&f.poses[0].held&&f.poses[0].joints[0]<2,"single spike must not drag track");
 s.person(1,1);s.next();f=s.run(p);check(f.poses[0].track==id&&!f.poses[0].held,"recover from spike");
 s.session=2;s.next();check(s.run(p).poses.empty(),"epoch reset");s.next();s.run(p);s.ns-=100000000;check(s.run(p).poses.empty(),"time regression reset");
 s.poses[0]=std::numeric_limits<float>::quiet_NaN();bool rejected=false;try{s.run(p);}catch(...){rejected=true;}check(rejected,"nonfinite rejected");
 Postprocessor multi;Sample m;m.person(1,0);m.person(2,2);m.person(3,4);m.person(4,6,.7f);auto before=m.poses;m.run(multi);m.next();auto mf=m.run(multi);check(mf.poses.size()==3,"top3 cap");check(m.poses==before,"immutable raw");
 m.scores[1]=.7;m.scores[2]=.9;m.next();auto mf2=m.run(multi);check(mf2.poses[0].track==mf.poses[0].track,"rank reorder keeps ID ordering");
 Postprocessor pending;Sample q;q.person(0,0);q.run(pending);q.next();q.scores.fill(0);q.run(pending);q.person(0,0);q.next();check(q.run(pending).poses.empty(),"nonconsecutive confirmation");q.next();check(q.run(pending).poses.size()==1,"consecutive confirmation after miss");
 q.person(0,10);q.next(110);auto displaced=q.run(pending);check(displaced.poses.size()==1&&displaced.poses[0].held,"persistent displacement first observation");q.next(61);displaced=q.run(pending);check(displaced.poses.size()==2&&!displaced.poses[0].held&&displaced.poses[0].joints[0]>9,"persistent new location confirmed before old expires");
 Postprocessor crossing;Sample c;std::uint64_t left=0,right=0;
 for(unsigned n=0;n<18;++n){c.scores.fill(0);c.person(n%2?2:1,-.7+.09*n);c.person(n%2?1:2,.7-.09*n);
  // Distinct relative skeletons remain distinguishable as centres cross.
  for(unsigned j=0;j<14;++j)c.poses[(n%2?1:2)*42+j*3+2]+=(j%2?.35f:-.35f);
  auto cf=c.run(crossing);if(n==1){left=cf.poses[0].track;right=cf.poses[1].track;}
  if(n>1){check(cf.poses.size()==2,"crossing count");for(const auto& person:cf.poses){check(person.track==left||person.track==right,"crossing identity rebuild");check(person.candidate==(person.track==left?(n%2?2u:1u):(n%2?1u:2u)),"crossing swapped identities");}}c.next(n%2?61:110);}
 OneEuro noise;std::mt19937 rng(42);std::normal_distribution<double> n(0,.025);double raw=0,filtered=0;
 for(unsigned i=0;i<1000;++i){double x=n(rng),y=noise.update(x,1./15,{});if(i>100){raw+=x*x;filtered+=y*y;}}
 const double reduction=1-std::sqrt(filtered/raw);check(reduction>=.4,"jitter target");
 OneEuro moving;std::vector<double> truth,shown;for(unsigned i=0;i<600;++i){double x=std::sin(i/15.*6.283185307179586);truth.push_back(x);shown.push_back(moving.update(x,1./15,{}));}
 unsigned lag=0;double minerr=1e99;for(unsigned k=0;k<5;++k){double err=0;for(unsigned i=100;i<600;++i)err+=std::pow(shown[i]-truth[i-k],2);if(err<minerr){minerr=err;lag=k;}}check(lag<=1,"15Hz motion latency target");
 std::cout<<"{\"passed\":true,\"jitter_reduction\":"<<reduction<<",\"motion_lag_ms\":"<<lag*1000./15<<"}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
