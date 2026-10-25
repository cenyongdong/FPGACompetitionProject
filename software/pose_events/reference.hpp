#pragma once
#include <array>
#include <cstdint>
#include <string>

// Independent owned-value PS prototype: no SDK, graph, MMIO, networking or PL IO.
namespace pose::events {
    using Ns = std::uint64_t;
    struct Vec3 { double x = 0, y = 0, z = 0; };
    enum class Clock { Unknown, VerifiedCapture, Synthetic };
    enum class Origin { Unknown, ArchivedInference, VerifiedLive, Synthetic };
    enum class Stance { Unknown, Standing, Sitting };
    enum class Trunk { Unknown, Upright, Leaning };
    enum class Arms { Unknown, Down, Raised };
    enum class Help { Unknown, Ready, Holding, Latched, AwaitRelease };
    enum class Availability { Initializing, Unverified, Synthetic, Available,
                              NoReliablePose, InputStale, ResultStale, ServiceLost, Stopped, Fault };
    enum Reason : std::uint32_t {
        None = 0, MappingUnknown = 1, UpUnknown = 2, TimeUnknown = 4,
        SubjectUnknown = 8, InvalidPose = 16, Degenerate = 32,
        Discontinuity = 64, LowScore = 128, Duplicate = 256,
        OriginUnknown = 512, IdentityUnknown = 1024
    };
    // Named indices must be supplied with evidence. Project topology alone is not a map.
    struct Joints {
        int shoulder_l = -1, shoulder_r = -1, hip_l = -1, hip_r = -1;
        int knee_l = -1, knee_r = -1, ankle_l = -1, ankle_r = -1;
        int elbow_l = -1, elbow_r = -1, wrist_l = -1, wrist_r = -1;
    };
    struct Contract {
        bool mapping_verified = false, up_verified = false;
        Joints joints;
        Vec3 up;
        std::string mapping_evidence, up_evidence;
    };
    struct Config {
        Contract contract;
        // Uncalibrated engineering thresholds, not medical probabilities/criteria.
        double score_min = 0.5;
        double knee_stand_enter = 155, knee_stand_exit = 140;
        double knee_sit_enter = 120, knee_sit_exit = 135;
        double lean_enter = 35, lean_exit = 25;
        double wrist_enter_ratio = 0.20, wrist_exit_ratio = 0.10;
        Ns confirm_ns = 300000000, hold_ns = 1000000000, release_ns = 500000000;
        Ns max_capture_gap_ns = 150000000;
    };
    struct Frame {
        Ns now_ns = 0, capture_ns = 0;
        std::uint64_t epoch = 0, sequence = 0, capture_sequence = 0;
        std::string segment;
        Clock clock = Clock::Unknown;
        Origin origin = Origin::Unknown;
        // Explicit external single-subject evidence; score/candidate slot is not identity.
        bool subject_verified = false;
        float score = 0;
        std::array<float, 42> coordinates {};
    };
    struct Output {
        Stance stance = Stance::Unknown;
        Trunk trunk = Trunk::Unknown;
        Arms arms = Arms::Unknown;
        Help help = Help::Unknown;
        std::uint32_t reasons = None;
        double knee_degrees = 0, trunk_degrees = 0, wrist_ratio = 0;
        unsigned raised_mask = 0; // bit0/bit1 are the explicitly mapped left/right arms.
        bool features_valid = false, event_created = false, request_pending = false;
        std::uint64_t event_id = 0, event_epoch = 0;
    };
    class Processor {
    public:
        explicit Processor(Config config = {});
        Output observe(const Frame& frame);
        bool acknowledge(std::uint64_t event_epoch, std::uint64_t event_id);
        void break_continuity();
        const Output& latest() const { return latest_; }
    private:
        Config config_;
        Output latest_;
        bool have_previous_ = false, stance_pending_ = false, trunk_pending_ = false;
        bool hold_active_ = false, release_active_ = false, released_ = true;
        Frame previous_; // One owned frame; bounded memory, no unbounded history.
        Stance pending_stance_ = Stance::Unknown;
        Trunk pending_trunk_ = Trunk::Unknown;
        Ns stance_begin_ = 0, trunk_begin_ = 0, hold_begin_ = 0, release_begin_ = 0;
        std::uint64_t next_event_ = 1;
        unsigned holding_arms_ = 0;
    };
    struct Feedback {
        Availability availability = Availability::Initializing;
        bool service_alive = false, input_recent = false, result_recent = false, request_pending = false;
        std::uint64_t event_id = 0, event_epoch = 0;
    };
    // Virtual-time model only. Never connects to hardware or asserts DMA completion.
    class PlSimulator {
    public:
        PlSimulator(Ns service_timeout_ns = 500000000, Ns result_timeout_ns = 300000000);
        void begin(Ns now, std::uint64_t epoch);
        bool heartbeat(Ns now, std::uint64_t epoch, std::uint64_t sequence);
        bool input(Ns now, std::uint64_t epoch, std::uint64_t sequence);
        bool result(const Frame& frame, const Output& output);
        bool acknowledge(Ns now, std::uint64_t event_epoch, std::uint64_t event_id);
        void stop(Ns now, bool fault = false);
        Feedback tick(Ns now);
    private:
        void time(Ns now);
        Ns service_timeout_, result_timeout_, now_ = 0, began_ = 0;
        Ns last_heartbeat_ = 0, last_input_ = 0, last_result_ = 0;
        std::uint64_t epoch_ = 0, heartbeat_sequence_ = 0, input_sequence_ = 0, result_sequence_ = 0;
        bool started_ = false, have_heartbeat_ = false, have_input_ = false, have_result_ = false;
        bool stopped_ = false, fault_ = false;
        Feedback feedback_;
        Availability reported_ = Availability::Unverified;
    };
    const char* name(Stance); const char* name(Trunk); const char* name(Arms);
    const char* name(Help); const char* name(Availability);
}
