#pragma once
#include "stream.hpp"

namespace pose::vitals {
struct ReceiverSample {
    std::uint64_t session=0,time_ns=0,event_sequence=0;
    std::array<AntennaPair,channels> pairs{};
    bool valid=true;
};
struct Resampled {
    bool reset=false;
    std::string reason;
    std::uint64_t epoch=1;
    std::vector<PhaseSample> samples;
};
// Single receiver, same-event antenna pairs. Relative RX time remains explicit.
// Causal implementation of the established 600Hz / 481-tap / 50Hz adapter.
// A source jump/gap clears history instead of filtering over it.
class ReceiverResampler {
    bool have_=false;
    ReceiverSample previous_{};
    std::array<double,channels> wrapped_{},unwrapped_{};
    std::array<std::uint64_t,channels> last_bad_ns_{};
    std::array<bool,channels> broken_{};
    std::array<std::array<double,channels>,481> dense_{};
    std::uint64_t base_ns_=0,next_dense_=0,epoch_=1,sequence_=0;
    std::size_t write_=0,filled_=0;
    void initialize(const ReceiverSample&,const std::array<double,channels>&);
    void append(const std::array<double,channels>&,std::uint64_t,Resampled&);
public:
    Resampled push(const ReceiverSample&);
    void invalidate();
};
class ReceiverStream {
    ReceiverResampler resampler_;
    PhaseStream stream_;
public:
    ReceiverStream(PhaseClock clock,std::string evidence,CorrelationBackend* backend=nullptr)
      :stream_(clock,std::move(evidence),{},backend){}
    std::vector<StreamUpdate> push(const ReceiverSample&);
    StreamUpdate invalidate(const std::string& reason="source_unavailable") {
        resampler_.invalidate(); return stream_.invalidate(reason);
    }
};
}
