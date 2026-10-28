#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace pose::post {
using Joints=std::array<float,42>;
struct Config {
    double min_cutoff=1, beta=0.5, d_cutoff=1;
    // Tracking must not inherit the lag (or tuning) of presentation smoothing.
    double tracking_cutoff=3, velocity_cutoff=1;
    std::uint64_t hold_ns=250000000;
    // CPU replay experiment only when >hold_ns (PL supports dt<=250 ms).
    // Default stays 250 ms: longer retention sustained false hypotheses.
    std::uint64_t identity_ns=250000000;
    // Both tests must pass: nearby distinct skeletons are not duplicates.
    double duplicate_centre=0.3, duplicate_pose=0.3;
    // Reject nearly translated copies as well as almost identical coordinates.
    double duplicate_translation=0.7, duplicate_shape=0.2;
    unsigned confirmation_hits=3;
    std::optional<float> score_threshold=0.2f; // nullopt disables score filtering.
    unsigned top_k=3;
};
struct Identity { std::uint64_t session=0, frame=0, sequence=0, source_ns=0; };
struct Person {
    std::uint64_t track=0, observed_ns=0;
    unsigned candidate=0; float score=0; Joints joints{}; bool held=false;
};
struct GeometrySummary {
    std::array<std::array<double,3>,3> centres{};
    std::array<double,3> radii{};
    unsigned duplicates=0;
};
struct FilterUpdate {std::uint64_t track;Joints observation;double dt;bool initialize;};
struct PresentationFrame {
    Identity id; std::vector<Person> poses, raw_poses;
    std::uint64_t hold_ns=250000000;
    std::optional<float> score_threshold=0.2f;
    unsigned top_k=3;
    std::string json(bool replay=false) const;
};
struct Metrics {
    std::uint64_t births=0,expired=0,duplicates=0,rejected_pairs=0,resets=0,confirmation_total_ns=0,confirmation_max_ns=0,display_duplicates=0;
    std::uint64_t history_selections=0,reacquired=0,held_handoffs=0,hidden_frames=0,shadow_deferred=0;
    std::uint64_t joint_gate_rejections=0,bone_gate_rejections=0;
    // Wall-clock CPU time around confirmed-track coordinate filtering only.
    std::uint64_t cpu_filter_frames=0,cpu_filter_coordinates=0,cpu_filter_ns=0,cpu_filter_max_ns=0;
};
// Optional explicitly selected backend; CPU remains the production default.
// Called only for current confirmed tracks after display-slot selection.
class FilterBackend {
public:
    virtual ~FilterBackend()=default;
    virtual void reset()=0;
    virtual void begin_frame(const std::vector<Person>&)=0;
    virtual Joints update(std::uint64_t track,const Joints&,double dt,bool initialize)=0;
    virtual std::vector<Joints> update_batch(const std::vector<FilterUpdate>& updates){
        std::vector<Joints> result;for(const auto& u:updates)result.push_back(update(u.track,u.observation,u.dt,u.initialize));return result;
    }
    virtual bool geometry(const std::vector<Person>&,GeometrySummary&,bool){return false;}
};
class OneEuro {
    bool initialized_=false;
    double x_=0,y_=0,d_=0;
public:
    void reset(){initialized_=false;}
    double update(double x,double dt,const Config& c);
};
class Postprocessor {
    struct Track {
        Person value; std::array<double,3> centre{},association_centre{},velocity{};
        Joints observation{}; double radius=0.25,dt=0; unsigned hits=0;
        Joints previous_observation{},filtered{};
        double support=0;
        bool initialize=false,retired=false;
        std::uint64_t first_ns=0;
        std::array<OneEuro,42> filter;
    };
    Config config_; FilterBackend* backend_; std::vector<Track> tracks_; Identity previous_{};
    std::uint64_t next_id_=1; Metrics metrics_;
public:
    explicit Postprocessor(Config c={},FilterBackend* backend=nullptr):config_(c),backend_(backend){}
    void reset();
    void set_backend(FilterBackend* backend){backend_=backend;reset();}
    PresentationFrame update(const Identity&,const float* scores,const float* poses);
    const Metrics& metrics()const{return metrics_;}
};
}
