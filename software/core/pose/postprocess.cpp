#include "postprocess.hpp"
#include <algorithm>
#include <chrono>
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
bool duplicate(const Person&a,const Person&b,const Config&config){
 const auto ac=centre(a.joints),bc=centre(b.joints);
 const double scale=std::max(radius(a.joints,ac),radius(b.joints,bc));
 double sq=0;for(unsigned j=0;j<42;++j)sq+=std::pow(double(a.joints[j])-b.joints[j],2);
 const double cd=distance(ac,bc),full=std::sqrt(sq/14);
 return (cd<config.duplicate_centre*scale&&full<config.duplicate_pose*scale)||
        (cd<config.duplicate_translation*scale&&shape(a.joints,ac,b.joints,bc)<config.duplicate_shape*scale);
}
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
 if(!std::isfinite(config_.min_cutoff)||!std::isfinite(config_.d_cutoff)||!std::isfinite(config_.beta)||config_.min_cutoff<=0||config_.d_cutoff<=0||config_.beta<0||!config_.hold_ns||!std::isfinite(config_.duplicate_centre)||!std::isfinite(config_.duplicate_pose)||config_.duplicate_centre<=0||config_.duplicate_pose<=0)throw std::runtime_error("Invalid postprocess configuration");
 if(config_.identity_ns<config_.hold_ns||config_.identity_ns>1000000000ull||config_.confirmation_hits<2||config_.confirmation_hits>4||!std::isfinite(config_.duplicate_translation)||!std::isfinite(config_.duplicate_shape)||config_.duplicate_translation<0||config_.duplicate_shape<0)throw std::runtime_error("Invalid confirmation/duplicate configuration");
 if(previous_.session && (id.session!=previous_.session||id.source_ns<=previous_.source_ns||id.sequence<=previous_.sequence))reset();
 previous_=id;
 PresentationFrame out;out.id=id;out.hold_ns=config_.hold_ns;
 std::array<unsigned,180> rank{};std::iota(rank.begin(),rank.end(),0);
 std::partial_sort(rank.begin(),rank.begin()+3,rank.end(),[&](auto a,auto b){return scores[a]==scores[b]?a<b:scores[a]>scores[b];});
 std::vector<Person> detections;std::vector<Centre> centres;std::vector<double> radii;
 for(unsigned n=0;n<3;++n){const auto i=rank[n];if(!(scores[i]>0.2f))continue;
  Person p;p.candidate=i;p.score=scores[i];p.observed_ns=id.source_ns;std::copy_n(poses+42*i,42,p.joints.begin());out.raw_poses.push_back(p);
  const auto c=centre(p.joints);const double r=radius(p.joints,c);
  detections.push_back(p);centres.push_back(c);radii.push_back(r);
 }
 tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[&](const Track&t){
  const auto lifetime=t.hits>=config_.confirmation_hits?config_.identity_ns:config_.hold_ns;
  if(id.source_ns-t.value.observed_ns>lifetime){++metrics_.expired;return true;}return false;
 }),tracks_.end());
 // Candidate-index order makes equal-cost assignments independent of score order.
 std::vector<unsigned> order(detections.size());std::iota(order.begin(),order.end(),0);
 std::sort(order.begin(),order.end(),[&](unsigned a,unsigned b){return detections[a].candidate<detections[b].candidate;});
 auto old_detections=detections;auto old_centres=centres;auto old_radii=radii;
 for(unsigned d=0;d<order.size();++d){detections[d]=old_detections[order[d]];centres[d]=old_centres[order[d]];radii[d]=old_radii[order[d]];}
 const unsigned nt=unsigned(tracks_.size()),nd=unsigned(detections.size());
 std::array<std::array<bool,3>,3> conflicts{};
 for(unsigned a=0;a<nd;++a)for(unsigned b=0;b<a;++b)
  conflicts[a][b]=conflicts[b][a]=duplicate(detections[a],detections[b],config_);
 std::array<std::array<double,3>,6> costs{};
 for(unsigned t=0;t<nt;++t)for(unsigned d=0;d<nd;++d){const auto&tr=tracks_[t];const double dt=double(id.source_ns-tr.value.observed_ns)/1e9,scale=std::max(tr.radius,radii[d]);
  const bool dormant=id.source_ns-tr.value.observed_ns>config_.hold_ns;
  // Predict from the committed filtered centre. A single noisy observation
  // must not move both the pose and the next association gate in one step.
  auto prediction=tr.hits>=config_.confirmation_hits?centre(tr.value.joints):tr.centre;
  if(!dormant)for(unsigned a=0;a<3;++a)prediction[a]+=tr.velocity[a]*dt;
  const double cd=distance(prediction,centres[d])/scale,sd=shape(tr.observation,tr.centre,detections[d].joints,centres[d])/scale;
  // Hidden identity is only reacquired near its last observation, without
  // extrapolating a stale velocity or relaxing the gate with the longer gap.
  costs[t][d]=(cd<=(dormant?.5:0.5+4*dt)&&sd<=(dormant?.3:0.5+6*dt))?cd+sd:std::numeric_limits<double>::infinity();
  if(!std::isfinite(costs[t][d]))++metrics_.rejected_pairs;
 }
 // Select a representative jointly with association. Conflicting detections
 // cannot consume two tracks; all Top3 candidates remain in raw_poses.
 // Preserve live confirmed identities first, then dormant ones, then pending.
 std::array<int,3> current{{-1,-1,-1}},best=current,best_counts{{-1,-1,-1}};
 double best_cost=0;
 std::function<void(unsigned,unsigned,std::array<int,3>,double)> visit=[&](unsigned d,unsigned used,std::array<int,3> counts,double cost){
  if(d==nd){if(counts>best_counts||(counts==best_counts&&cost<best_cost)){best_counts=counts;best_cost=cost;best=current;}return;}
  bool conflict=false;for(unsigned k=0;k<d;++k)conflict|=current[k]>=0&&conflicts[d][k];
  if(!conflict)for(unsigned t=0;t<nt;++t)if(!(used&(1u<<t))&&std::isfinite(costs[t][d])){
   const auto&tr=tracks_[t];const unsigned priority=tr.hits<config_.confirmation_hits?2:id.source_ns-tr.value.observed_ns>config_.hold_ns?1:0;
   auto next=counts;++next[priority];current[d]=int(t);visit(d+1,used|(1u<<t),next,cost+costs[t][d]);
  }
  current[d]=-1;visit(d+1,used,counts,cost);
 };visit(0,0,{{0,0,0}},0);
 std::array<bool,3> selected{};
 for(unsigned d=0;d<nd;++d)selected[d]=best[d]>=0;
 // Unmatched groups retain the original score / equal-score index ordering.
 for(const auto&raw:out.raw_poses)for(unsigned d=0;d<nd;++d)if(detections[d].candidate==raw.candidate&&!selected[d]){
  bool conflict=false;for(unsigned k=0;k<nd;++k)conflict|=selected[k]&&conflicts[d][k];
  if(conflict)++metrics_.duplicates;else selected[d]=true;
 }
 for(unsigned d=0;d<nd;++d)if(selected[d]&&best[d]>=0)for(unsigned k=0;k<nd;++k)
  if(!selected[k]&&conflicts[d][k]&&(detections[k].score>detections[d].score||(detections[k].score==detections[d].score&&detections[k].candidate<detections[d].candidate)))++metrics_.history_selections;
 for(auto&t:tracks_){t.value.held=true;t.initialize=false;}
 std::uint64_t cpu_filter_ns=0,cpu_filter_coordinates=0;
 for(unsigned d=0;d<nd;++d){if(best[d]<0)continue;auto&t=tracks_[unsigned(best[d])];const double dt=double(id.source_ns-t.value.observed_ns)/1e9;
  const bool dormant=id.source_ns-t.value.observed_ns>config_.hold_ns;
  if(dormant)++metrics_.reacquired;
  for(unsigned a=0;a<3;++a){const double measured=(centres[d][a]-t.centre[a])/dt;const double cap=4*std::max(t.radius,radii[d]);
   t.velocity[a]=dormant?0:t.velocity[a]+alpha(config_.d_cutoff,dt)*(std::clamp(measured,-cap,cap)-t.velocity[a]);}
  const auto track=t.value.track;t.value=detections[d];t.value.track=track;
  t.support+=alpha(1,dt)*(detections[d].score-t.support);
  t.dt=dt;
  t.previous_observation=t.observation;t.observation=detections[d].joints;t.centre=centres[d];t.radius=radii[d];
  ++t.hits;t.initialize=t.hits==config_.confirmation_hits;
 }
 // A weak newborn that repeatedly resembles an established nearby body is
 // ambiguous. Keep observing it before allocating a second visible person.
 // This is NOT a global score threshold: independent / equally supported
 // neighbours and far weak targets retain the normal three-hit confirmation.
 for(auto&fresh:tracks_)if(fresh.initialize){
  for(const auto&old:tracks_)if(!old.initialize&&old.hits>=config_.confirmation_hits&&old.first_ns<fresh.first_ns&&old.support-fresh.support>.25){
   const auto oc=centre(old.filtered);const double old_radius=radius(old.filtered,oc);
   auto resembles=[&](const Joints&j){const auto c=centre(j);const double scale=std::max(old_radius,radius(j,c));
    return distance(c,oc)<scale&&shape(j,c,old.filtered,oc)<.25*scale;};
   if(resembles(fresh.previous_observation)&&resembles(fresh.observation)){
    --fresh.hits;fresh.initialize=false;++metrics_.shadow_deferred;break;
   }
  }
 }
 // A newly confirmed hypothesis may be a replacement for a missed identity.
 // Require two spatial/shape witnesses and no simultaneous observations during
 // confirmation. Mere proximity of two established people never triggers this.
 auto near_observation=[&](const Joints&a,const Track&b){const auto ac=centre(a);const double scale=std::max(radius(a,ac),b.radius);
  return distance(ac,b.centre)<.8*scale&&shape(a,ac,b.observation,b.centre)<.25*scale;};
 for(auto&fresh:tracks_)if(fresh.initialize){
  Track* owner=nullptr;unsigned choices=0;
  for(auto&old:tracks_)if(old.hits>=config_.confirmation_hits&&old.value.held&&!old.retired&&old.value.observed_ns<fresh.first_ns&&
      near_observation(fresh.previous_observation,old)&&near_observation(fresh.observation,old)){owner=&old;++choices;}
  if(choices!=1)continue; // Ambiguous re-identification remains separate.
  const auto old_id=owner->value.track;const auto last_ns=owner->value.observed_ns;
  owner->previous_observation=owner->observation;owner->observation=fresh.observation;
  owner->centre=fresh.centre;owner->radius=fresh.radius;owner->velocity={};
  owner->support=fresh.support;
  owner->value=fresh.value;owner->value.track=old_id;owner->dt=double(id.source_ns-last_ns)/1e9;
  ++owner->hits;owner->initialize=false;fresh.retired=true;++metrics_.held_handoffs;
 }
 tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[](const Track&t){return t.retired;}),tracks_.end());
 for(const auto&t:tracks_)if(t.initialize){++metrics_.births;const auto ns=id.source_ns-t.first_ns;metrics_.confirmation_total_ns+=ns;metrics_.confirmation_max_ns=std::max(metrics_.confirmation_max_ns,ns);}
 // A missed observation breaks consecutive-observation confirmation.
 tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[&](const Track&t){return t.hits<config_.confirmation_hits&&t.value.held;}),tracks_.end());
 for(unsigned d=0;d<nd;++d)if(selected[d]&&best[d]<0){
  auto pending=std::count_if(tracks_.begin(),tracks_.end(),[&](const Track&t){return t.hits<config_.confirmation_hits;});
  if(pending>=3)continue;
  Track t;t.value=detections[d];t.value.track=next_id_++;t.hits=1;t.first_ns=id.source_ns;t.centre=centres[d];t.radius=radii[d];t.observation=t.value.joints;t.support=t.value.score;
  tracks_.push_back(t);
 }
 // Keep a bounded set of confirmed tracks; current observations win over held ones.
 std::stable_sort(tracks_.begin(),tracks_.end(),[&](const Track&a,const Track&b){
  auto priority=[&](const Track&t){return t.hits<config_.confirmation_hits?3:t.value.held?2:t.hits==config_.confirmation_hits?1:0;};
  return priority(a)!=priority(b)?priority(a)<priority(b):a.value.track<b.value.track;
 });
 unsigned confirmed=0;tracks_.erase(std::remove_if(tracks_.begin(),tracks_.end(),[&](const Track&t){return t.hits>=config_.confirmation_hits&&++confirmed>3;}),tracks_.end());
 if(backend_){std::vector<Person> active;for(const auto&t:tracks_)if(t.hits>=config_.confirmation_hits)active.push_back(t.value);backend_->begin_frame(active);}
 for(auto&t:tracks_)if(t.hits>=config_.confirmation_hits&&!t.value.held){
  if(backend_)t.value.joints=backend_->update(t.value.track,t.observation,t.dt,t.initialize);
  else{const auto begin=std::chrono::steady_clock::now();
   for(unsigned j=0;j<42;++j){if(t.initialize)t.filter[j].reset();t.value.joints[j]=float(t.filter[j].update(t.observation[j],t.dt,config_));}
   cpu_filter_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count();cpu_filter_coordinates+=42;
  }
  t.filtered=t.value.joints;
 }
 // Filtering/holding can bring otherwise separate observations together. Apply
 // the same spatial rule to the actual displayed poses, in display priority
 // order, without merging identities or extending a held observation's life.
 for(const auto&t:tracks_)if(t.hits>=config_.confirmation_hits){
  if(id.source_ns-t.value.observed_ns>config_.hold_ns){++metrics_.hidden_frames;continue;}
  if(std::any_of(out.poses.begin(),out.poses.end(),[&](const Person&kept){return duplicate(t.value,kept,config_);}))++metrics_.display_duplicates;
  else out.poses.push_back(t.value);
 }
 std::sort(tracks_.begin(),tracks_.end(),[](const Track&a,const Track&b){return a.value.track<b.value.track;});
 if(cpu_filter_coordinates){++metrics_.cpu_filter_frames;metrics_.cpu_filter_coordinates+=cpu_filter_coordinates;
  metrics_.cpu_filter_ns+=cpu_filter_ns;metrics_.cpu_filter_max_ns=std::max(metrics_.cpu_filter_max_ns,cpu_filter_ns);}
 return out;
}
std::string PresentationFrame::json(bool replay)const{
 std::ostringstream o;o<<std::setprecision(9)<<"{\"schema\":\"PIWVIEW1\",\"version\":1,\"replay\":"<<(replay?"true":"false")
 <<",\"session\":\""<<id.session<<"\",\"frame\":\""<<id.frame<<"\",\"sequence\":\""<<id.sequence<<"\",\"source_ns\":\""<<id.source_ns
 <<"\",\"hold_ms\":"<<double(hold_ns)/1e6<<",\"poses\":";people(o,poses,*this);o<<",\"raw_poses\":";people(o,raw_poses,*this);o<<"}\n";
 auto s=o.str();if(s.size()>16384)throw std::runtime_error("Presentation record oversized");return s;
}
}
