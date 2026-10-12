#pragma once
#include "pipeline_fixture_source.hpp"
#include <functional>
#include <optional>
#include <thread>
namespace pose::model_only {
struct Attempt {
    size_t index=0;uint64_t fixtureFrame=0;
    std::string caseName;pose_v1::Window window;
};
struct Returned {Attempt attempt;pose_v1::application::Result result;bool verified=false;};
// Own fixture windows and returned values; one owner, no SDK or timer side effects.
class Run {
    std::thread::id owner_=std::this_thread::get_id();
    std::vector<pose::validation::FixtureWindow> cases_;
    size_t limit_,attempts_=0;bool stopped_=false;
    std::optional<Attempt> current_;
    std::vector<Returned> returned_;
    void owner()const;
public:
    using Process=std::function<pose_v1::application::Result(const pose_v1::Window&)>;
    using SaveThenVerify=std::function<void(const pose::validation::FixtureWindow&,const Returned&)>;
    Run(std::vector<pose::validation::FixtureWindow>,size_t limit);
    void step(const Process&,const SaveThenVerify&);
    const std::vector<Returned>& returned()const;
    const std::optional<Attempt>& current()const;
    size_t attempts()const;
    bool stopped()const;
};
uint64_t scheduledStart(uint64_t epoch,size_t index,uint64_t previousStart,uint64_t period);
}
