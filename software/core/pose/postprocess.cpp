#include "postprocess.hpp"
#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>

namespace pose::post {
namespace {
using Centre=std::array<double,3>;
Centre centre(const Joints& p){Centre c{};for(unsigned j=0;j<14;++j)for(unsigned a=0;a<3;++a)c[a]+=p[3*j+a]/14.0;return c;}
double radius(const Joints& p,const Centre& c){double v=0;for(unsigned j=0;j<14;++j)for(unsigned a=0;a<3;++a)v+=std::pow(p[3*j+a]-c[a],2);return std::max(0.25,std::sqrt(v/14));}
double distance(const Centre& a,const Centre& b){double v=0;for(unsigned i=0;i<3;++i)v+=std::pow(a[i]-b[i],2);return std::sqrt(v);}
double shape(const Joints&a,const Centre&ac,const Joints&b,const Centre&bc){double v=0;for(unsigned i=0;i<42;++i)v+=std::pow((a[i]-ac[i%3])-(b[i]-bc[i%3]),2);return std::sqrt(v/14);}
double alpha(double cutoff,double dt){const auto t=6.283185307179586*cutoff*dt;return t/(1+t);}
void people(std::ostream&o,const std::vector<Person>&ps,const PresentationFrame&f){
 o<<'[';bool comma=false;for(const auto&p:ps){if(comma)o<<',';comma=true;
 o<<"{\"track\":\""<<p.track<<"\",\"candidate\":"<<p.candidate<<",\"score\":"<<p.score
  <<",\"held\":"<<(p.held?"true":"false")<<",\"observed_ns\":\""<<p.observed_ns
  <<"\",\"age_ms\":"<<double(f.id.source_ns-p.observed_ns)/1e6<<",\"joints\":[";
 for(unsigned i=0;i<42;++i){if(i)o<<',';o<<p.joints[i];}o<<"]}";}o<<']';
}
}
double OneEuro::update(double x,double dt,const Config&c){
 if(!std::isfinite(x)||!std::isfinite(dt)||dt<0)throw std::runtime_error("Invalid filter sample");
 if(!initialized_){initialized_=true;x_=y_=x;d_=0;return x;}
 if(dt<=0)throw std::runtime_error("Nonpositive filter interval");
 const double ad=alpha(c.d_cutoff,dt);d_+=ad*((x-x_)/dt-d_);x_=x;
 const double a=alpha(c.min_cutoff+c.beta*std::abs(d_),dt);y_+=a*(x-y_);return y_;
}
void Postprocessor::reset(){tracks_.clear();previous_={};if(backend_)backend_->reset();++metrics_.resets;}
PresentationFrame Postprocessor::update(const Identity&id,const float*scores,const float*poses){
 if(!scores||!poses||!id.session||!id.sequence||!id.source_ns)throw std::runtime_error("Invalid presentation identity");
 for(unsigned i=0;i<180;++i)if(!std::isfinite(scores[i]))throw std::runtime_error("Nonfinite presentation score");
 for(unsigned i=0;i<7560;++i)if(!std::isfinite(poses[i]))throw std::runtime_error("Nonfinite presentation coordinates");
 if(!std::isfinite(config_.min_cutoff)||!std::isfinite(config_.d_cutoff)||!std::isfinite(config_.beta)||config_.min_cutoff<=0||config_.d_cutoff<=0||config_.beta<0||!config_.hold_ns)throw std::runtime_error("Invalid postprocess configuration");
 if(previous_.session && (id.session!=previous_.session||id.source_ns<=previous_.source_ns||id.sequence<=previous_.sequence))reset();
 previous_=id;
 PresentationFrame out;out.id=id;out.hold_ns=config_.hold_ns;
 std::array<unsigned,180> rank{};std::iota(rank.begin(),rank.end(),0);
 std::partial_sort(rank.begin(),rank.begin()+3,rank.end(),[&](auto a,auto b){return scores[a]==scores[b]?a<b:scores[a]>scores[b];});
 std::vector<Person> detections;std::vector<Centre> centres;std::vector<double> radii;
 for(unsigned n=0;n<3;++n){const auto i=rank[n];if(!(scores[i]>0.2f))continue;
  Person p;p.candidate=i;p.score=scores[i];p.observed_ns=id.source_ns;std::copy_n(poses+42*i,42,p.joints.begin());out.raw_poses.push_back(p);
  const auto c=centre(p.joints);const double r=radius(p.joints,c);bool duplicate=false;
  for(unsigned k=0;k<detections.size();++k){double sq=0;for(unsigned j=0;j<42;++j)sq+=std::pow(double(p.joints[j])-detections[k].joints[j],2);
   const double scale=std::max(r,radii[k]);if(distance(c,centres[k])<0.2*scale&&std::sqrt(sq/14)<0.2*scale)duplicate=true;}
  if(duplicate){++metrics_.duplicates;continue;}detections.push_back(p);centres.push_back(c);radii.push_back(r);
 }
 tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[&](const Track&t){if(id.source_ns-t.value.observed_ns>config_.hold_ns){++metrics_.expired;return true;}return false;}),tracks_.end());
 // Candidate-index order makes equal-cost assignments independent of score order.
 std::vector<unsigned> order(detections.size());std::iota(order.begin(),order.end(),0);
 std::sort(order.begin(),order.end(),[&](unsigned a,unsigned b){return detections[a].candidate<detections[b].candidate;});
 auto old_detections=detections;auto old_centres=centres;auto old_radii=radii;
 for(unsigned d=0;d<order.size();++d){detections[d]=old_detections[order[d]];centres[d]=old_centres[order[d]];radii[d]=old_radii[order[d]];}
 const unsigned nt=unsigned(tracks_.size()),nd=unsigned(detections.size());
 std::array<std::array<double,3>,6> costs{};
 for(unsigned t=0;t<nt;++t)for(unsigned d=0;d<nd;++d){const auto&tr=tracks_[t];const double dt=double(id.source_ns-tr.value.observed_ns)/1e9,scale=std::max(tr.radius,radii[d]);
  auto prediction=tr.centre;for(unsigned a=0;a<3;++a)prediction[a]+=tr.velocity[a]*dt;
  const double cd=distance(prediction,centres[d])/scale,sd=shape(tr.observation,tr.centre,detections[d].joints,centres[d])/scale;
  costs[t][d]=(cd<=0.5+4*dt&&sd<=0.5+6*dt)?cd+sd:std::numeric_limits<double>::infinity();
  if(!std::isfinite(costs[t][d]))++metrics_.rejected_pairs;
 }
 // At most 7^3 assignments. Unmatched is explored last; equal costs prefer older IDs.
 std::array<int,3> current{{-1,-1,-1}},best=current;int best_count=-1;double best_cost=0;
 std::function<void(unsigned,unsigned,int,double)> visit=[&](unsigned d,unsigned used,int count,double cost){
  if(d==nd){if(count>best_count||(count==best_count&&cost<best_cost)){best_count=count;best_cost=cost;best=current;}return;}
  for(unsigned t=0;t<nt;++t)if(!(used&(1u<<t))&&std::isfinite(costs[t][d])){current[d]=int(t);visit(d+1,used|(1u<<t),count+1,cost+costs[t][d]);}
  current[d]=-1;visit(d+1,used,count,cost);
 };visit(0,0,0,0);
 for(auto&t:tracks_)t.value.held=true;
 for(unsigned d=0;d<nd;++d){if(best[d]<0)continue;auto&t=tracks_[unsigned(best[d])];const double dt=double(id.source_ns-t.value.observed_ns)/1e9;
  for(unsigned a=0;a<3;++a){const double measured=(centres[d][a]-t.centre[a])/dt;const double cap=4*std::max(t.radius,radii[d]);t.velocity[a]=std::clamp(measured,-cap,cap);}
  const auto track=t.value.track;t.value=detections[d];t.value.track=track;
  t.dt=dt;
  if(!backend_)for(unsigned j=0;j<42;++j){if(t.hits==1)t.filter[j].reset();t.value.joints[j]=float(t.filter[j].update(detections[d].joints[j],dt,config_));}
  t.observation=detections[d].joints;t.centre=centres[d];t.radius=radii[d];if(t.hits==1){++metrics_.births;auto ns=std::uint64_t(std::llround(dt*1e9));metrics_.confirmation_total_ns+=ns;metrics_.confirmation_max_ns=std::max(metrics_.confirmation_max_ns,ns);}++t.hits;
 }
 // A missed observation breaks the two-consecutive-matches confirmation rule.
 tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[](const Track&t){return t.hits==1&&t.value.held;}),tracks_.end());
 for(unsigned d=0;d<nd;++d)if(best[d]<0){
  auto pending=std::count_if(tracks_.begin(),tracks_.end(),[](const Track&t){return t.hits<2;});
  if(pending>=3)continue;
  Track t;t.value=detections[d];t.value.track=next_id_++;t.hits=1;t.centre=centres[d];t.radius=radii[d];t.observation=t.value.joints;
  for(unsigned j=0;j<42;++j)t.filter[j].update(t.value.joints[j],0,config_);
  tracks_.push_back(t);
 }
 // Keep a bounded set of confirmed tracks; current observations win over held ones.
 std::stable_sort(tracks_.begin(),tracks_.end(),[](const Track&a,const Track&b){
  auto priority=[](const Track&t){return t.hits<2?3:t.value.held?2:t.hits==2?1:0;};
  return priority(a)!=priority(b)?priority(a)<priority(b):a.value.track<b.value.track;
 });
 unsigned confirmed=0;tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[&](const Track&t){return t.hits>=2&&++confirmed>3;}),tracks_.end());
 if(backend_){std::vector<Person> active;for(const auto&t:tracks_)if(t.hits>=2)active.push_back(t.value);backend_->begin_frame(active);
  for(auto&t:tracks_)if(t.hits>=2&&!t.value.held)t.value.joints=backend_->update(t.value.track,t.observation,t.dt,t.hits==2);}
 for(const auto&t:tracks_)if(t.hits>=2)out.poses.push_back(t.value);
 std::sort(tracks_.begin(),tracks_.end(),[](const Track&a,const Track&b){return a.value.track<b.value.track;});
 return out;
}
std::string PresentationFrame::json(bool replay)const{
 std::ostringstream o;o<<std::setprecision(9)<<"{\"schema\":\"PIWVIEW1\",\"version\":1,\"replay\":"<<(replay?"true":"false")
 <<",\"session\":\""<<id.session<<"\",\"frame\":\""<<id.frame<<"\",\"sequence\":\""<<id.sequence<<"\",\"source_ns\":\""<<id.source_ns
 <<"\",\"hold_ms\":"<<double(hold_ns)/1e6<<",\"poses\":";people(o,poses,*this);o<<",\"raw_poses\":";people(o,raw_poses,*this);o<<"}\n";
 auto s=o.str();if(s.size()>16384)throw std::runtime_error("Presentation record oversized");return s;
}
}
