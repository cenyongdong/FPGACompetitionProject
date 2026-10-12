#pragma once
#include <exception>
#include <functional>
#include <thread>
namespace pose::load_lifecycle {
struct Hooks {
    std::function<void()> start,waitReady,check,join;
    std::function<void(bool)> requestStop;
};
// Main-owner lifecycle only. Hooks own their hardware; no SDK or video details.
class Control {
    const std::thread::id owner_=std::this_thread::get_id();
    enum class State {idle,attempted,ready,joined};State state_=State::idle;
    bool enabled_;Hooks hooks_;
    void owner()const;
public:
    Control(bool enabled,Hooks);
    void start();
    void check()const;
    // Each cleanup hook is attempted, preserving the first computation error.
    void finish(std::exception_ptr&);
    bool joined()const;
};
}
