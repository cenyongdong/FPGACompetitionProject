// Independent fixed-load diagnostic. Never linked into the normal Engine path.
#include <icraft-xrt/core/device.h>
#include "ai_monitor_sdk.hpp"
#include "ai_read_monitor_sdk.hpp"

#include <algorithm>
#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <initializer_list>
#include <ostream>
#include <stdexcept>
#include <streambuf>
#include <string>
#include <vector>
#include <fcntl.h>
#include <unistd.h>

namespace {

constexpr std::array<std::size_t, 4> kSizes{{64, 4096, 65536, 1048576}};

std::runtime_error io_error(const std::string& operation, const std::string& path) {
    const int saved_errno = errno;
    return std::runtime_error(operation + ": " + path + ": " + std::strerror(saved_errno));
}

// O_EXCL prevents evidence replacement. No buffered userspace bytes remain
// when _Exit preserves the SDK's possibly in-flight allocation after a fault.
class ExclusiveLogBuffer final : public std::streambuf {
public:
    explicit ExclusiveLogBuffer(const std::string& path)
        : fd_(::open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600)) {
        if (fd_ < 0) throw io_error("Cannot create fresh trace", path);
    }
    ~ExclusiveLogBuffer() override { if (fd_ >= 0) ::close(fd_); }
    ExclusiveLogBuffer(const ExclusiveLogBuffer&) = delete;
    ExclusiveLogBuffer& operator=(const ExclusiveLogBuffer&) = delete;
    void commit() {
        if (!okay_) throw std::runtime_error("Evidence trace write previously failed");
        while (::fsync(fd_) != 0) {
            if (errno != EINTR) throw io_error("Trace fsync failed", "trace");
        }
    }
protected:
    std::streamsize xsputn(const char* data, std::streamsize bytes) override {
        std::streamsize written = 0;
        while (written < bytes) {
            const auto result = ::write(fd_, data + written, static_cast<std::size_t>(bytes - written));
            if (result < 0 && errno == EINTR) continue;
            if (result <= 0) { okay_ = false; break; }
            written += static_cast<std::streamsize>(result);
        }
        return written;
    }
    int_type overflow(int_type value) override {
        if (traits_type::eq_int_type(value, traits_type::eof())) return traits_type::not_eof(value);
        const char byte = traits_type::to_char_type(value);
        return xsputn(&byte, 1) == 1 ? value : traits_type::eof();
    }
    int sync() override { return okay_ ? 0 : -1; }
private:
    int fd_ = -1;
    bool okay_ = true;
};

class EvidenceLog final {
public:
    explicit EvidenceLog(const std::string& path) : buffer_(path), stream_(&buffer_) {}
    std::ostream& stream() noexcept { return stream_; }
    void commit() {
        stream_.flush();
        if (!stream_) throw std::runtime_error("Evidence trace stream failed");
        buffer_.commit();
    }
private:
    ExclusiveLogBuffer buffer_;
    std::ostream stream_;
};

std::string quoted(const std::string& value) {
    constexpr char digits[] = "0123456789abcdef";
    std::string result = "\"";
    for (const unsigned char byte : value) {
        if (byte == '"' || byte == '\\') {
            result.push_back('\\'); result.push_back(static_cast<char>(byte));
        } else if (byte < 0x20) {
            result += "\\u00";
            result.push_back(digits[byte >> 4]); result.push_back(digits[byte & 0x0f]);
        } else result.push_back(static_cast<char>(byte));
    }
    result.push_back('"');
    return result;
}

std::string artifact(const std::string& trace, std::size_t bytes, const char* role) {
    return trace + "." + std::to_string(bytes) + "." + role + ".bin";
}

void save_binary_fresh(const std::string& path, const std::vector<char>& bytes) {
    const int fd = ::open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd < 0) throw io_error("Cannot create fresh binary evidence", path);
    try {
        std::size_t written = 0;
        while (written < bytes.size()) {
            const auto count = ::write(fd, bytes.data() + written, bytes.size() - written);
            if (count < 0 && errno == EINTR) continue;
            if (count <= 0) {
                if (count == 0) errno = EIO;
                throw io_error("Binary evidence write failed", path);
            }
            written += static_cast<std::size_t>(count);
        }
        while (::fsync(fd) != 0) {
            if (errno != EINTR) throw io_error("Binary evidence fsync failed", path);
        }
    } catch (...) {
        ::close(fd);
        throw;
    }
    if (::close(fd) != 0) throw io_error("Binary evidence close failed", path);
}

void flush_log(std::ostream& log) {
    log.flush();
    if (!log) throw std::runtime_error("Evidence trace write failed");
}

// Best-effort diagnostics never replace the original transfer/data error.
// Every command lifecycle is single attempt, including the old v2 monitor.
void capture_after_stop(const icraft::xrt::Device& device, pose::ai_read_monitor::Capture& capture,
                        std::ostream& log, bool& mig_attempted) noexcept {
    if (!capture.was_armed()) {
        std::cerr << "AI_READ_MONITOR_SKIPPED ARM not completed; no legal FREEZE or MIG snapshot" << std::endl;
    }
    if (capture.can_freeze()) {
        try { static_cast<void>(capture.freeze()); }
        catch (const std::exception& diagnostic) {
            std::cerr << "AI_READ_MONITOR_CAPTURE_FAILED " << diagnostic.what() << std::endl;
        } catch (...) {
            std::cerr << "AI_READ_MONITOR_CAPTURE_FAILED unknown exception" << std::endl;
        }
    }
    try { capture.save_cached(); }
    catch (const std::exception& diagnostic) {
        std::cerr << "AI_READ_MONITOR_CACHE_SAVE_FAILED " << diagnostic.what() << std::endl;
    } catch (...) {
        std::cerr << "AI_READ_MONITOR_CACHE_SAVE_FAILED unknown exception" << std::endl;
    }
    if (!mig_attempted && capture.was_armed()) {
        mig_attempted = true;
        try { pose::ai_monitor::save(device, log); }
        catch (const std::exception& diagnostic) {
            std::cerr << "AI_MIG_MONITOR_CAPTURE_FAILED " << diagnostic.what() << std::endl;
        } catch (...) {
            std::cerr << "AI_MIG_MONITOR_CAPTURE_FAILED unknown exception" << std::endl;
        }
    }
}

// No legal FREEZE exists until this process has completed its ARM. Preserve
// failures of Open/identity/status SDK calls without inventing that ownership.
template <typename Operation>
decltype(auto) pre_arm_sdk(const char* phase, Operation operation) {
    try { return operation(); }
    catch (const std::exception& original) {
        std::cerr << "AI_READ_DMA_SDK_STOP " << phase << " " << original.what() << std::endl;
        std::cerr << "AI_READ_MONITOR_SKIPPED ARM not completed; no legal FREEZE" << std::endl;
        std::_Exit(71);
    }
}

void commit_after_stop(EvidenceLog& evidence) noexcept {
    try { evidence.commit(); }
    catch (const std::exception& diagnostic) {
        std::cerr << "AI_READ_DMA_EVIDENCE_COMMIT_FAILED " << diagnostic.what() << std::endl;
    } catch (...) {
        std::cerr << "AI_READ_DMA_EVIDENCE_COMMIT_FAILED unknown exception" << std::endl;
    }
}

[[noreturn]] void stop_sdk(const char* phase, const std::exception& original,
                         const icraft::xrt::Device& device, pose::ai_read_monitor::Capture& capture,
                         EvidenceLog& evidence, bool& mig_attempted) {
    // Original SDK exception goes to stderr before any capture/secondary I/O.
    std::cerr << "AI_READ_DMA_SDK_STOP " << phase << " " << original.what() << std::endl;
    auto& log = evidence.stream();
    log << "{\"event\":\"SDK_exception_stop_allocation_retained\",\"phase\":" << quoted(phase) << "}\n";
    capture_after_stop(device, capture, log, mig_attempted);
    commit_after_stop(evidence);
    std::_Exit(71);
}

int run_probe(const std::string& trace) {
    EvidenceLog evidence(trace);
    auto& log = evidence.stream();
    // The regular files are created only after a successful read. Check all
    // names before opening the device; O_EXCL also protects against later races.
    for (const auto bytes : kSizes) {
        for (const auto role : {"source", "actual"}) {
            if (std::filesystem::exists(artifact(trace, bytes, role)))
                throw std::runtime_error("Binary evidence path already exists; no Device::Open");
        }
    }
    auto device = pre_arm_sdk("Device::Open", [] {
        return icraft::xrt::Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000");
    });
    pre_arm_sdk("setWaitTime", [&] { device.setWaitTime(1000); });
    const auto versions = pre_arm_sdk("version", [&] { return device.version(); });
    if (versions.at("device") != "25122301" || versions.at("icore") != "FMSHZGV3TECH-AID - 24160628")
        throw std::runtime_error("Device identity changed; no DMA");
    const auto& regs = pre_arm_sdk("defaultRegRegion", [&]() -> decltype(auto) { return device.defaultRegRegion(); });
    if (pre_arm_sdk("initial_DMA_status", [&] { return regs.read(0x40584, true); }) != 0)
        throw std::runtime_error("Initial SDK DMA status is not zero; no transfer");
    auto region = pre_arm_sdk("defaultMemRegion", [&] { return device.defaultMemRegion(); });
    if (pre_arm_sdk("region_type", [&] { return std::string(region->typeKey()); }) != "AXIZG330AIPLDDRMemRegionNode")
        throw std::runtime_error("PL DDR region changed; no transfer");
    pose::ai_read_monitor::Capture capture(device, log);
    // Only the observer state is cleared. This command cannot reset a DMA,
    // bridge, HP port, memory controller, SDK session, or protected AI path.
    bool mig_attempted = false;
    try { capture.arm(); }
    catch (const pose::ai_read_monitor::MonitorError& original) {
        std::cerr << "AI_READ_DMA_PRETRANSFER_STOP " << original.what() << std::endl;
        commit_after_stop(evidence);
        return 1;
    } catch (const std::exception& original) {
        stop_sdk("ARM", original, device, capture, evidence, mig_attempted);
    }
    auto chunk = [&]() {
        try { return region.malloc(1048576, false, 64); }
        catch (const std::exception& original) {
            stop_sdk("malloc", original, device, capture, evidence, mig_attempted);
        }
    }();
    try {
        log << "{\"event\":\"allocation\",\"address\":" << chunk->begin.addr()
            << ",\"bytes\":" << chunk->byte_size << ",\"alignment\":64}\n";
        flush_log(log);
        if (chunk->byte_size != 1048576 || chunk->begin.addr() % 64 != 0)
            throw std::runtime_error("Actual allocation size/alignment changed; no DMA");
        for (const auto bytes : kSizes) {
            std::vector<char> source(bytes), actual(bytes);
            for (std::size_t i = 0; i < bytes; ++i)
                source[i] = static_cast<char>((i * 37) ^ (i >> 9) ^ bytes);
            log << "{\"event\":\"write_begin\",\"bytes\":" << bytes << "}\n";
            flush_log(log);
            const char* phase = "write";
            try {
                chunk.write(0, source.data(), bytes);
                phase = "post_write_status";
                const auto status = regs.read(0x40584, true);
                log << "{\"event\":\"write_returned\",\"bytes\":" << bytes
                    << ",\"status\":" << status << "}\n";
                phase = "read";
                chunk.read(actual.data(), 0, bytes);
            } catch (const std::exception& original) {
                stop_sdk(phase, original, device, capture, evidence, mig_attempted);
            }
            // Saving precedes comparison. A failed/unreturned read creates no
            // actual file. Partial I/O artifacts remain evidence, never PASS.
            const auto source_path = artifact(trace, bytes, "source");
            const auto actual_path = artifact(trace, bytes, "actual");
            save_binary_fresh(source_path, source);
            save_binary_fresh(actual_path, actual);
            log << "{\"event\":\"read_returned_and_complete_bytes_saved\",\"bytes\":" << bytes
                << ",\"source\":" << quoted(source_path) << ",\"actual\":" << quoted(actual_path) << "}\n";
            flush_log(log);
            if (source != actual) {
                const auto mismatch = std::mismatch(source.begin(), source.end(), actual.begin());
                const auto offset = static_cast<std::size_t>(mismatch.first - source.begin());
                std::cerr << "AI_READ_DMA_DATA_STOP bytes=" << bytes << " first_offset=" << offset << std::endl;
                log << "{\"event\":\"mismatch_stop_allocation_retained\",\"bytes\":" << bytes
                    << ",\"first_offset\":" << offset << ",\"source_byte\":"
                    << static_cast<unsigned>(static_cast<unsigned char>(*mismatch.first))
                    << ",\"actual_byte\":" << static_cast<unsigned>(static_cast<unsigned char>(*mismatch.second)) << "}\n";
                capture_after_stop(device, capture, log, mig_attempted);
                commit_after_stop(evidence);
                std::_Exit(72);
            }
            log << "{\"event\":\"roundtrip_pass\",\"bytes\":" << bytes << "}\n";
            flush_log(log);
        }
        // No snapshot or synchronization was inserted between the four loads.
        try { static_cast<void>(capture.freeze()); }
        catch (const std::exception& original) {
            stop_sdk("final_read_monitor_capture", original, device, capture, evidence, mig_attempted);
        }
        mig_attempted = true;
        try { pose::ai_monitor::save(device, log); }
        catch (const std::exception& original) {
            stop_sdk("final_MIG_monitor_capture", original, device, capture, evidence, mig_attempted);
        }
        try { chunk.free(); }
        catch (const std::exception& original) {
            stop_sdk("free", original, device, capture, evidence, mig_attempted);
        }
        log << "{\"event\":\"completed_and_released\"}\n";
        evidence.commit();
        std::cout << "AI_READ_DMA_ROUNDTRIP_PASS" << std::endl;
        return 0;
    } catch (const std::exception& original) {
        std::cerr << "AI_READ_DMA_DIAGNOSTIC_IO_STOP " << original.what() << std::endl;
        capture_after_stop(device, capture, log, mig_attempted);
        commit_after_stop(evidence);
        std::_Exit(74);
    }
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 2 || std::string(argv[1]).empty())
            throw std::runtime_error("One fresh trace path required; no optional load sizes or retries");
        if (!std::filesystem::path(argv[1]).is_absolute())
            throw std::runtime_error("Absolute fresh trace path required");
        return run_probe(argv[1]);
    } catch (const std::exception& original) {
        std::cerr << "AI_READ_DMA_PRETRANSFER_STOP " << original.what() << std::endl;
        return 1;
    }
}
