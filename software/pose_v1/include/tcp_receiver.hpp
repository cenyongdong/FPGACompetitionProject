#pragma once
#include "preprocess.hpp"
#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>

namespace pose_v1::transport {
using Clock=std::chrono::steady_clock;
constexpr size_t record_bytes=32+kPayloadBytes;
Window decode_record(const std::vector<unsigned char>&);
struct Item { Window window;uint64_t session=0,sequence=0;Clock::time_point arrived; };
// Only the unstarted window can be replaced; pop transfers ownership by value.
class LatestSlot {
    std::mutex mutex_;std::condition_variable cv_;std::optional<Item> item_;bool closed_=false;
public:
    bool push(Item item);
    bool clear();
    void close();
    std::optional<Item> pop(std::chrono::milliseconds wait);
    bool finished();
};
struct Stats { uint64_t sessions=0,received=0,rejected=0,overwritten=0,reconnect_discarded=0; };
class Receiver {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    Receiver(const std::string& address,uint16_t port,int idle_ms,size_t max_sessions);
    ~Receiver();
    Receiver(const Receiver&)=delete;Receiver& operator=(const Receiver&)=delete;
    std::optional<Item> pop(std::chrono::milliseconds wait);
    bool finished();Stats stats();std::vector<std::string> errors();uint16_t port()const;
    void stop();void check();
};
}
