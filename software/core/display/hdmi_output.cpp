#include "hdmi_output.hpp"
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>

namespace pose::hdmi {
    namespace {
        using Clock = std::chrono::steady_clock;
        void need(bool ok, const char* message) {
            if (!ok) throw std::runtime_error(message);
        }
    }

    struct Output::Impl {
        icraft::xrt::Device device;
        icraft::xrt::MemRegion region;
        icraft::xrt::MemChunk frames[2];
        std::ofstream log;
        std::thread::id owner = std::this_thread::get_id();
        uint32_t sequence = 0, lastId = 0;
        int current = -1;
        bool mayRead = false, closed = false;
        static constexpr uint64_t base = 0x400b0000;

        uint32_t rd(unsigned offset) const {
            return uint32_t(device.defaultRegRegion().read(base + offset));
        }
        void wr(unsigned offset, uint32_t value) const {
            device.defaultRegRegion().write(base + offset, value);
        }
        void checkThread() const {
            need(owner == std::this_thread::get_id(), "HDMI accessed outside owner thread");
        }
        Snapshot command(uint32_t op, uint32_t address = 0, uint32_t id = 0) {
            checkThread();
            need(!closed, "HDMI output already closed");
            need(rd(0x2c) == 0, "HDMI mailbox not ready or CSR error");
            const uint32_t issued = rd(0x24), replies = rd(0x28);
            need(issued == replies, "HDMI command already in flight");
            wr(0x04, address);
            wr(0x08, id);
            wr(0x0c, op);
            const auto deadline = Clock::now() + std::chrono::milliseconds(200);
            while (rd(0x28) == replies) {
                need(Clock::now() < deadline, "HDMI command response deadline");
                std::this_thread::sleep_for(std::chrono::microseconds(100));
            }
            need(rd(0x24) == issued + 1 && rd(0x28) == replies + 1,
                 "HDMI response generation mismatch");
            Snapshot s{rd(0x10), rd(0x14), rd(0x18), rd(0x1c), rd(0x20)};
            log << "{\"event\":\"command\",\"sequence\":" << ++sequence
                << ",\"op\":" << op << ",\"argument_address\":" << address
                << ",\"argument_id\":" << id << ",\"issued\":" << issued + 1
                << ",\"response\":" << replies + 1 << ",\"status\":" << s.status
                << ",\"stopped\":" << s.stopped << ",\"address\":" << s.address
                << ",\"accepted\":" << s.accepted << ",\"faults\":" << s.faults << "}\n";
            log.flush();
            need(bool(log), "HDMI evidence write failed");
            need(!(s.status & 0x80000000u), "HDMI command rejected");
            return s;
        }
        Snapshot healthy() {
            auto s = command(0);
            need(s.faults == 0 && (s.status & 0x40), "HDMI fault or PLL lock lost");
            need((rd(0x30) & 9) == 1 && rd(0x2c) == 0, "HDMI adapter/CSR fault");
            return s;
        }
        void stop() {
            // 即使发生欠载，也发一次STOP取得独立停止标签；不清故障或重试负载。
            const uint32_t tag = 0x70000000u | (sequence + 1);
            command(3, 0, tag);
            const auto deadline = Clock::now() + std::chrono::milliseconds(500);
            while (true) {
                auto s = command(0);
                if (s.idle() && s.stopped == tag && !(s.status & 0x3e)) break;
                need(Clock::now() < deadline, "HDMI STOP drain not proved; retain frames");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
            mayRead = false;
            log << "{\"event\":\"stop_proved\",\"tag\":" << tag << "}\n";
            log.flush();
        }
    };

    Output::Output(const icraft::xrt::Device& device, const std::filesystem::path& evidence)
        : impl_(std::make_unique<Impl>()) {
        auto& p = *impl_;
        p.device = device;
        need(!std::filesystem::exists(evidence), "Fresh HDMI evidence file required");
        p.log.open(evidence);
        need(bool(p.log), "Cannot open HDMI evidence");
        const auto versions = device.version();
        need(versions.at("device") == "25122301" &&
             versions.at("icore") == "FMSHZGV3TECH-AID - 24160628", "HDMI device identity differs");
        need(p.rd(0) == 0x48444d01 && p.rd(0x40) == 0x48445301, "HDMI candidate ABI absent");
        need(p.rd(0x44) == 148500000 && p.rd(0x48) == 742500000, "HDMI clock contract differs");
        const auto s = p.healthy();
        need(s.idle(), "HDMI not initially idle; existing owner must stop it");
        p.region = device.getMemRegion("udma");
        need(std::string(p.region->typeKey()) == "AXIZG330AIUdmaMemRegionNode", "HDMI UDMA region differs");
        for (int i = 0; i < 2; ++i) {
            // 禁止自动释放；显式STOP快照是唯一的帧块释放入口。
            p.frames[i] = p.region.malloc(frameBytes, false, 64);
            const auto address = p.frames[i]->begin.addr();
            need(p.frames[i].isOn(p.region) && p.frames[i]->byte_size == frameBytes &&
                 address >= 0x30100000 && address + frameBytes <= 0x38100000 &&
                 address % 64 == 0, "Allocated HDMI frame outside validated bounds");
            p.log << "{\"event\":\"allocation\",\"slot\":" << i << ",\"address\":" << address
                  << ",\"bytes\":" << frameBytes << ",\"pointer_type\":"
                  << int(p.frames[i]->begin.ptype()) << "}\n";
        }
        const uint64_t a = p.frames[0]->begin.addr(), b = p.frames[1]->begin.addr();
        need(a + frameBytes <= b || b + frameBytes <= a, "HDMI frames overlap");
        p.log.flush();
    }

    void Output::verifyMemory() {
        auto& p = *impl_;
        p.checkThread();
        need(!p.mayRead && p.healthy().idle(), "Memory verification requires idle HDMI");
        std::vector<uint8_t> source(frameBytes), actual(frameBytes);
        for (int i = 0; i < 2; ++i) {
            for (size_t n = 0; n < source.size(); ++n) source[n] = uint8_t((n * 37) ^ (n >> 9) ^ (i * 0x95));
            p.frames[i].write(0, reinterpret_cast<char*>(source.data()), source.size());
            p.frames[i].read(reinterpret_cast<char*>(actual.data()), 0, actual.size());
            need(source == actual, "Full HDMI SDK write/read mismatch");
            p.log << "{\"event\":\"memory_verified\",\"slot\":" << i << ",\"bytes\":" << frameBytes << "}\n";
        }
        p.log.flush();
    }

    void Output::show(const std::vector<uint8_t>& rgb565, uint32_t frameId) {
        auto& p = *impl_;
        p.checkThread();
        need(rgb565.size() == frameBytes && frameId != 0 && frameId != p.lastId,
             "HDMI frame size or ID invalid");
        p.healthy();
        const int slot = p.current < 0 ? 0 : 1 - p.current;
        const auto begin = Clock::now();
        // SDK公开UDMA write包含其设备侧同步；不自行解引用ADDR/BOTH或补猜测cache操作。
        p.frames[slot].write(0, reinterpret_cast<char*>(const_cast<uint8_t*>(rgb565.data())), rgb565.size());
        const uint32_t address = uint32_t(p.frames[slot]->begin.addr());
        if (!p.mayRead) {
            p.wr(0x34, 0);
            need(p.rd(0x34) == 0, "Cannot disable static HDMI pattern");
            p.mayRead = true; // START发布前即保护内存，后续任何错误都必须STOP。
            p.command(1, address, frameId);
        } else {
            p.command(2, address, frameId);
        }
        const auto deadline = Clock::now() + std::chrono::milliseconds(200);
        while (true) {
            const auto s = p.healthy();
            if (s.accepted == frameId && s.address == address && !(s.status & 0x10)) break;
            need(Clock::now() < deadline, "HDMI frame adoption deadline");
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        p.current = slot;
        p.lastId = frameId;
        p.log << "{\"event\":\"adopted\",\"id\":" << frameId << ",\"slot\":" << slot
              << ",\"address\":" << address << ",\"write_and_adopt_ms\":"
              << std::chrono::duration<double, std::milli>(Clock::now() - begin).count() << "}\n";
        p.log.flush();
    }

    Snapshot Output::observe() { return impl_->healthy(); }

    void Output::close() {
        auto& p = *impl_;
        p.checkThread();
        if (p.closed) return;
        p.stop();
        for (auto& frame : p.frames) frame.free();
        p.closed = true;
        p.log << "{\"event\":\"frames_released_after_stop\"}\n";
        p.log.flush();
    }

    Output::~Output() {
        if (impl_ && !impl_->closed) {
            try { close(); }
            catch (const std::exception& e) {
                std::cerr << "HDMI_RELEASE_WITHHELD " << e.what() << std::endl;
                // 无STOP证明时不运行SDK析构／释放；保留日志及物理块身份，禁止继续新负载。
                std::_Exit(70);
            }
        }
    }
}
