#include "tcp_sender.hpp"
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <chrono>

int main(int argc, char** argv) {
    try {
        if (argc != 5 && argc != 6) throw std::runtime_error("Expected records.piwpose IPv4 port interval_ms [fragment_bytes]");
        const auto port = std::stoul(argv[3]), interval = std::stoul(argv[4]);
        const auto fragment = argc == 6 ? std::stoul(argv[5]) : pose::output::record_bytes;
        if (!port || port > 65535 || interval > 10000 || !fragment || fragment > 256) throw std::runtime_error("Replay options out of bounds");
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) throw std::runtime_error("Cannot open real-result records");
        std::vector<pose::output::Frame> frames;
        pose::output::Record record;
        while (file.read(reinterpret_cast<char*>(record.data()), record.size())) {
            auto frame = pose::output::decode(record);
            if (pose::output::encode(frame) != record) throw std::runtime_error("C++ codec roundtrip differs");
            frames.push_back(frame);
            if (frames.size() > 10000) throw std::runtime_error("Replay budget exceeded");
        }
        if (!file.eof() || file.gcount() || frames.empty()) throw std::runtime_error("Empty or truncated real-result records");
        pose::output::TcpSender sender(argv[2], static_cast<std::uint16_t>(port));
        for (std::size_t i = 0; i < frames.size(); ++i) {
            if (i) std::this_thread::sleep_for(std::chrono::milliseconds(interval));
            sender.send(frames[i], static_cast<unsigned>(fragment));
            std::cout << "{\"sent_frame\":\"" << frames[i].frame << "\",\"sequence\":\"" << frames[i].sequence << "\",\"bytes\":256}" << std::endl;
        }
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "POSE_REPLAY_STOP " << e.what() << std::endl;
        return 1;
    }
}
