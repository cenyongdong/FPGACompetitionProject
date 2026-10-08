#pragma once
#include "pipeline_fixture_source.hpp"
#include "tcp_receiver.hpp"

namespace pose::measurement {
using Clock=std::chrono::steady_clock;
inline uint64_t timestamp(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
constexpr uint64_t transportBase=100000;
constexpr size_t sentLimit=33, warmups=3;
// Transport identity is separate from fixture identity, including overwritten windows.
const pose::validation::FixtureWindow& fixtureFor(const std::vector<pose::validation::FixtureWindow>&,uint64_t transportId);
void verify(const pose::validation::FixtureWindow&,const pose_v1::application::Result&,const pose_v1::Window&,size_t invocation);
struct Measurement {
    pose_v1::transport::Item item;
    pose_v1::application::Result result;
    uint64_t dequeued=0,processBegin=0,processEnd=0,verifyEnd=0,drawEnd=0,convertEnd=0,published=0;
};
// No hardware access. Dump owned values before applying the unchanged strict oracle.
void save(const std::vector<Measurement>&,const std::vector<pose::validation::FixtureWindow>&,
          const std::filesystem::path&);
}
