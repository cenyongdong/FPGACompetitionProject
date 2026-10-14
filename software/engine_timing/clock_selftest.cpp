// SDK无关采样合同：阻塞/异常标记、线程归属和容量上限，绝不打开设备。
#include "application_clock.hpp"
#include <chrono>
#include <iostream>
#include <string>
#include <thread>

namespace fc = pose_v1::forward_clock;

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("CASE NEW_OUTPUT_DIR required");
        const std::string mode = argv[1];
        const std::filesystem::path output = argv[2];
        if (!std::filesystem::create_directory(output)) throw std::runtime_error("Fresh output required");
        fc::configure(1);
        fc::start(99, 0, fc::Clock::now());
        if (mode == "basic") {
            {
                fc::Span total("synthetic.total");
                { fc::Span sleep("synthetic.blocking"); std::this_thread::sleep_for(std::chrono::milliseconds(2)); }
                try { fc::Span failure("synthetic.exception"); throw std::runtime_error("expected"); }
                catch (const std::runtime_error&) {}
            }
            if (fc::records.size() != 3 || !fc::records[1].failed || fc::records[0].failed || fc::records[2].failed)
                throw std::runtime_error("Exception/record coverage differs");
            if (fc::records[0].end - fc::records[0].begin < 1000000) throw std::runtime_error("Blocking wall clock missing");
#ifdef __linux__
            for (const auto& row : fc::records) {
                if (!row.first.cpu_valid || !row.last.cpu_valid || !row.first.usage_valid || !row.last.usage_valid ||
                    row.last.cpu_ns < row.first.cpu_ns) throw std::runtime_error("Linux thread CPU/rusage sample missing");
            }
#endif
            fc::check();
            fc::save(output / "trace.jsonl");
            fc::save_transfers(output / "transfers.jsonl");
        } else if (mode == "thread") {
            std::thread unexpected([] { const auto t = fc::Clock::now(); fc::record("wrong.thread", 0, 0, t, t); });
            unexpected.join();
            bool rejected = false;
            try { fc::check(); } catch (const std::runtime_error&) { rejected = true; }
            if (!rejected || !fc::records.empty()) throw std::runtime_error("Unexpected thread accepted");
        } else if (mode == "capacity") {
            const auto t = fc::Clock::now();
            for (size_t i = 0; i <= fc::record_limit; ++i) fc::record("bounded", i, 0, t, t);
            bool rejected = false;
            try { fc::save(output / "partial.jsonl"); } catch (const std::runtime_error&) { rejected = true; }
            if (!rejected || fc::records.size() != fc::record_limit || !std::filesystem::exists(output / "partial.jsonl"))
                throw std::runtime_error("Capacity failure lost evidence");
        } else throw std::runtime_error("Unknown selftest case");
        std::cout << mode << ": SDK-free contract passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
