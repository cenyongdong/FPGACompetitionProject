#include "bounded_queue.hpp"
#include <atomic>
#include <chrono>
#include <future>
#include <memory>
#include <thread>
#include <stdexcept>
#include <iostream>
using namespace std::chrono_literals;
void need(bool yes,const char* text){if(!yes)throw std::runtime_error(text);}
int main() {
    // 原故障触发条件：30Hz、8帧容量、消费者在保存回执处停400ms。
    demo_v1::Queue<std::unique_ptr<int>> queue(8);
    std::atomic<int> got{0};
    auto consumer=std::async(std::launch::async,[&]{
        while(auto p=queue.pop()) {
            need(**p==got++,"FIFO/owned value mismatch");
            if(**p==2)std::this_thread::sleep_for(400ms);
        }
    });
    auto start=std::chrono::steady_clock::now();size_t blocked=0;
    for(int n=0;n<40;++n) {
        std::this_thread::sleep_until(start+std::chrono::milliseconds(n*33));
        auto value=std::make_unique<int>(n);auto begin=std::chrono::steady_clock::now();
        queue.wait_push(std::move(value),1000ms);
        if(std::chrono::steady_clock::now()-begin>1ms)++blocked;
    }
    queue.close();consumer.get();need(got==40&&blocked>0&&queue.high_water()==8,"Delay did not exercise bounded backpressure");
    demo_v1::Queue<std::unique_ptr<int>> stalled(1);stalled.push(std::make_unique<int>(7));auto retained=std::make_unique<int>(8);
    bool expired=false;try{stalled.wait_push(std::move(retained),20ms);}catch(...){expired=true;}
    need(expired&&retained&&*retained==8,"Deadline destroyed original");
    auto waiting=std::async(std::launch::async,[&]{try{stalled.wait_push(std::move(retained),1000ms);}catch(const std::exception& e){return std::string(e.what());}return std::string();});
    std::this_thread::sleep_for(20ms);stalled.fail(std::make_exception_ptr(std::runtime_error("first failure")));
    need(waiting.get()=="first failure"&&retained&&*retained==8,"Failure failed to wake producer/preserve original");
    std::cout<<"30Hz/400ms save pause: FIFO exact, capacity8, bounded wait, deadline and first failure preserved\n";
}
