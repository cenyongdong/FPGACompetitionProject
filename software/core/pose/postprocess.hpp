#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace pose::post {
using Joints=std::array<float,42>;
struct Config { double min_cutoff=1, beta=0.5, d_cutoff=1; std::uint64_t hold_ns=250000000; };
struct Identity { std::uint64_t session=0, frame=0, sequence=0, source_ns=0; };
struct Person {
    std::uint64_t track=0, observed_ns=0;
    unsigned candidate=0; float score=0; Joints joints{}; bool held=false;
};
struct PresentationFrame {
    Identity id; std::vector<Person> poses, raw_poses;
    std::uint64_t hold_ns=250000000;
    std::string json(bool replay=false) const;
};
struct Metrics { std::uint64_t births=0, expired=0, duplicates=0, rejected_pairs=0, resets=0,confirmation_total_ns=0,confirmation_max_ns=0; };
// Optional explicitly selected backend; CPU remains the production default.
// Called only for current confirmed tracks after display-slot selection.
class FilterBackend {
public:
    virtual ~FilterBackend()=default;
    virtual void reset()=0;
    virtual void begin_frame(const std::vector<Person>&)=0;
    virtual Joints update(std::uint64_t track,const Joints&,double dt,bool initialize)=0;
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
        Person value; std::array<double,3> centre{},velocity{};
        Joints observation{}; double radius=0.25,dt=0; unsigned hits=0;
        std::array<OneEuro,42> filter;
    };
    Config config_; FilterBackend* backend_; std::vector<Track> tracks_; Identity previous_{};
    std::uint64_t next_id_=1; Metrics metrics_;
public:
    explicit Postprocessor(Config c={},FilterBackend* backend=nullptr):config_(c),backend_(backend){}
    void reset();
    PresentationFrame update(const Identity&,const float* scores,const float* poses);
    const Metrics& metrics()const{return metrics_;}
};
}
