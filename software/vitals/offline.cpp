#include "reference.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace {
    namespace fs = std::filesystem;
    using namespace pose::vitals;
    struct Input {
        Window window;
        Config config;
        std::string origin = "unknown", clock_evidence;
    };
    std::string trim(const std::string& text) {
        const auto first = text.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) return {};
        return text.substr(first, text.find_last_not_of(" \t\r\n") - first + 1);
    }
    std::vector<std::string> split(const std::string& line) {
        std::vector<std::string> values;
        std::size_t begin = 0;
        for (;;) {
            const auto end = line.find(',', begin);
            values.push_back(trim(line.substr(begin, end - begin)));
            if (end == std::string::npos) break;
            begin = end + 1;
        }
        return values;
    }
    std::uint64_t integer(const std::string& value) {
        if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
            throw std::runtime_error("Expected unsigned integer");
        std::size_t count;
        const auto out = std::stoull(value, &count);
        if (count != value.size()) throw std::runtime_error("Invalid integer");
        return out;
    }
    double number(const std::string& value) {
        std::size_t count;
        const auto out = std::stod(value, &count);
        if (count != value.size()) throw std::runtime_error("Invalid numeric field");
        return out;
    }
    std::string quoted(const std::string& text) {
        std::ostringstream out;
        out << '"';
        for (const auto c : text) {
            if (c == '\\' || c == '"') out << '\\' << c;
            else if (static_cast<unsigned char>(c) < 32)
                out << "\\u00" << std::hex << std::setw(2) << std::setfill('0') << unsigned(static_cast<unsigned char>(c));
            else out << c;
        }
        return out.str() + '"';
    }
    Input read(const fs::path& path, std::size_t offset) {
        if (!fs::is_regular_file(path) || fs::file_size(path) > 4 * 1024 * 1024)
            throw std::runtime_error("Input must be a regular CSV no larger than 4MiB");
        std::ifstream input(path);
        if (!input) throw std::runtime_error("Cannot open input");
        Input out;
        std::string line;
        bool header = false;
        std::set<std::string> metadata;
        std::size_t rows = 0;
        while (std::getline(input, line)) {
            if (line.size() > 4096) throw std::runtime_error("CSV line exceeds 4096 bytes");
            if (!header && !rows && line.compare(0, 3, "\xef\xbb\xbf") == 0) line.erase(0, 3);
            line = trim(line);
            if (line.empty()) continue;
            if (line[0] == '#') {
                if (header) throw std::runtime_error("Metadata must precede the CSV header");
                const auto equal = line.find('=');
                if (equal == std::string::npos) continue;
                const auto key = trim(line.substr(1, equal - 1)), value = trim(line.substr(equal + 1));
                if ((key == "sample_rate_hz" || key == "origin" || key == "clock" || key == "clock_evidence") &&
                    !metadata.insert(key).second)
                    throw std::runtime_error("Conflicting duplicate metadata: " + key);
                if (key == "sample_rate_hz") out.config.sample_rate = number(value);
                if (key == "origin") out.origin = value;
                if (key == "clock_evidence") out.clock_evidence = value;
                if (key == "clock") {
                    if (value == "synthetic_uniform") out.window.clock = ClockKind::SyntheticUniform;
                    else if (value == "verified_sampling") out.window.clock = ClockKind::VerifiedSampling;
                    else if (value == "unknown_arrival") out.window.clock = ClockKind::UnknownArrival;
                    else throw std::runtime_error("Unknown clock kind");
                }
                continue;
            }
            const auto fields = split(line);
            if (!header) {
                std::vector<std::string> expected{"time_ns", "sequence", "valid"};
                for (std::size_t ch = 0; ch < channels; ++ch)
                    for (const auto* name : {"ia", "qa", "ib", "qb"})
                        expected.push_back(std::string(name) + std::to_string(ch));
                if (fields != expected) throw std::runtime_error("Unsupported CSV columns");
                header = true;
                continue;
            }
            if (fields.size() != 3 + 4 * channels) throw std::runtime_error("Invalid CSV record width");
            if (++rows > 8192) throw std::runtime_error("CSV exceeds 8192 records");
            // 即使只分析一个窗口，也检查所有输入记录的解析，不接受坏尾部。
            Sample sample;
            sample.time_ns = integer(fields[0]);
            sample.sequence = integer(fields[1]);
            if (fields[2] != "0" && fields[2] != "1") throw std::runtime_error("Invalid valid flag");
            sample.valid = fields[2] == "1";
            for (std::size_t ch = 0; ch < channels; ++ch) {
                const auto k = 3 + ch * 4;
                sample.pairs[ch] = {{number(fields[k]), number(fields[k + 1])},
                                    {number(fields[k + 2]), number(fields[k + 3])}};
            }
            const auto required = out.config.sample_rate * (out.config.warmup_seconds + out.config.window_seconds);
            if (rows - 1 >= offset && out.window.samples.size() < max_samples &&
                static_cast<double>(out.window.samples.size()) < required)
                out.window.samples.push_back(sample);
        }
        if (!input.eof() || !header || !rows) throw std::runtime_error("CSV missing header/data or read failed");
        if (out.window.clock == ClockKind::SyntheticUniform && out.origin != "synthetic")
            throw std::runtime_error("Synthetic clock requires synthetic origin");
        if (out.window.clock == ClockKind::VerifiedSampling && out.clock_evidence.empty())
            throw std::runtime_error("Verified sampling requires explicit clock evidence");
        return out;
    }
    void values(std::ostream& out, const std::vector<double>& v) {
        out << '[';
        for (std::size_t i = 0; i < v.size(); ++i) {
            if (i) out << ',';
            if (!std::isfinite(v[i])) throw std::runtime_error("Non-finite evidence value");
            out << v[i];
        }
        out << ']';
    }
    void candidate(std::ostream& out, const Candidate& c) {
        out << "{\"usable\":" << (c.usable ? "true" : "false")
            << ",\"acf_hz\":" << c.acf_hz << ",\"spectral_hz\":" << c.spectral_hz
            << ",\"correlation\":" << c.correlation << ",\"concentration\":" << c.concentration
            << ",\"energy_ratio\":" << c.energy_ratio << ",\"reason\":" << quoted(c.reason) << '}';
    }
    void estimate(std::ostream& out, const std::optional<Estimate>& e) {
        if (!e) { out << "null"; return; }
        out << "{\"bpm\":" << e->bpm << ",\"confidence\":" << e->confidence
            << ",\"agreeing_channels\":" << e->agreeing_channels << '}';
    }
    void timing(std::ostream& out, const Timing& t) {
        out << "{\"quality_ms\":" << t.quality_ms << ",\"phase_ms\":" << t.phase_ms
            << ",\"filter_ms\":" << t.filter_ms << ",\"correlation_ms\":" << t.correlation_ms
            << ",\"spectrum_decision_ms\":" << t.spectrum_decision_ms << ",\"total_ms\":" << t.total_ms << '}';
    }
    double percentile(std::vector<double> v, double p) {
        std::sort(v.begin(), v.end());
        return v[static_cast<std::size_t>(std::ceil(v.size() * p)) - 1];
    }
    void summary(std::ostream& out, const Input& input, const Result& r, const fs::path& source,
                 const std::vector<Timing>& repeats, double cpu_ms) {
        out << std::setprecision(17);
        out << "{\"schema\":\"piw-vitals-reference-1\",\"algorithm\":\"phase-sos-acf-ps-v1\","
            << "\"hardware_test\":false,\"input_origin\":" << quoted(input.origin)
            << ",\"clock\":" << quoted(clock_name(input.window.clock))
            << ",\"clock_evidence\":" << quoted(input.clock_evidence)
            << ",\"correlation_backend\":" << quoted(r.correlation_backend)
            << ",\"source_csv\":" << quoted(fs::absolute(source).string())
            << ",\"sample_rate_hz\":" << input.config.sample_rate
            << ",\"warmup_seconds\":" << input.config.warmup_seconds
            << ",\"window_seconds\":" << input.config.window_seconds
            << ",\"status\":" << quoted(r.status) << ",\"reasons\":[";
        for (std::size_t i = 0; i < r.reasons.size(); ++i) {
            if (i) out << ',';
            out << quoted(r.reasons[i]);
        }
        const auto& q = r.quality;
        out << "],\"quality\":{\"samples\":" << q.samples << ",\"required_samples\":" << q.required_samples
            << ",\"missing_sequences\":" << q.missing_sequences << ",\"invalid_samples\":" << q.invalid_samples
            << ",\"jitter_p95_ms\":" << q.jitter_p95_ms << ",\"max_interval_ms\":" << q.max_interval_ms
            << "},\"heart\":";
        estimate(out, r.heart);
        out << ",\"breath\":"; estimate(out, r.breath);
        out << ",\"timing\":"; timing(out, r.timing);
        out << ",\"channels\":[";
        for (std::size_t ch = 0; ch < channels; ++ch) {
            if (ch) out << ',';
            out << "{\"heart\":"; candidate(out, r.trace[ch].heart_candidate);
            out << ",\"breath\":"; candidate(out, r.trace[ch].breath_candidate); out << '}';
        }
        out << "]";
        if (!repeats.empty()) {
            std::vector<double> times;
            for (const auto& t : repeats) times.push_back(t.total_ms);
            out << ",\"benchmark\":{\"scope\":\"host_algorithm_without_csv_or_json_io\",\"iterations\":"
                << repeats.size() << ",\"unique_input_windows\":1,\"p50_ms\":" << percentile(times, 0.5)
                << ",\"p95_ms\":" << percentile(times, 0.95) << ",\"p99_ms\":" << percentile(times, 0.99)
                << ",\"max_ms\":" << *std::max_element(times.begin(), times.end())
                << ",\"process_cpu_ms\":" << cpu_ms << ",\"host_threads\":" << std::thread::hardware_concurrency()
#ifdef __VERSION__
                << ",\"compiler\":" << quoted(__VERSION__)
#endif
                << ",\"per_iteration\":[";
            for (std::size_t i = 0; i < repeats.size(); ++i) {
                if (i) out << ',';
                timing(out, repeats[i]);
            }
            out << "]}";
        }
        out << "}\n";
    }
    void trace(std::ostream& out, const Result& result) {
        out << std::setprecision(17) << "{\"schema\":1,\"heart_sos\":[";
        auto sos = [&](const std::vector<Biquad>& sections) {
            for (std::size_t i = 0; i < sections.size(); ++i) {
                if (i) out << ',';
                const auto& c = sections[i];
                out << '[' << c.b0 << ',' << c.b1 << ',' << c.b2 << ",1," << c.a1 << ',' << c.a2 << ']';
            }
        };
        sos(result.heart_sections); out << "],\"breath_sos\":["; sos(result.breath_sections);
        out << "],\"channels\":[";
        for (std::size_t ch = 0; ch < channels; ++ch) {
            if (ch) out << ',';
            const auto& t = result.trace[ch];
            out << "{\"phase\":"; values(out, t.phase);
            out << ",\"detrended\":"; values(out, t.detrended);
            out << ",\"heart\":"; values(out, t.heart);
            out << ",\"breath\":"; values(out, t.breath);
            out << ",\"heart_acf\":"; values(out, t.heart_acf);
            out << ",\"breath_acf\":"; values(out, t.breath_acf); out << '}';
        }
        out << "]}\n";
    }
}

int main(int argc, char** argv) {
    try {
        fs::path input, output, trace_path;
        std::string correlation_backend="cpu";
        std::size_t repeat = 0, offset = 0;
        for (int i = 1; i < argc; ++i) {
            const std::string key = argv[i];
            if (i + 1 >= argc) throw std::runtime_error("Options require values");
            const std::string value = argv[++i];
            if (key == "--input") input = value;
            else if (key == "--output") output = value;
            else if (key == "--trace") trace_path = value;
            else if (key == "--repeat") repeat = static_cast<std::size_t>(integer(value));
            else if (key == "--offset") offset = static_cast<std::size_t>(integer(value));
            else if (key == "--correlation-backend") correlation_backend=value;
            else throw std::runtime_error("Unknown option: " + key);
        }
        if (input.empty() || output.empty() || repeat > 2000 || offset >= 8192)
            throw std::runtime_error("Expected --input CSV --output NEW_JSON [--trace NEW_JSON] [--repeat 0..2000] [--offset 0..8191]");
        if (fs::exists(output) || (!trace_path.empty() && fs::exists(trace_path)))
            throw std::runtime_error("Output already exists; preserve it and choose a new path");
        if (!trace_path.empty() && fs::absolute(output).lexically_normal() == fs::absolute(trace_path).lexically_normal())
            throw std::runtime_error("Summary and trace must use different paths");
        const auto data = read(input, offset);
        if(correlation_backend!="cpu"&&correlation_backend!="fixed-reference")throw std::runtime_error("Unknown correlation backend");
        ScalarDots dots;FixedCorrelation fixed(dots);
        CorrelationBackend* backend=correlation_backend=="cpu"?nullptr:&fixed;
        const auto result = analyze(data.window, data.config,backend);
        std::vector<Timing> repeats;
        const auto cpu_begin = std::clock();
        // 只有完整数据任务可以做耗时对照；不把快速拒绝路径作为算法吞吐。
        if (repeat && result.status == "invalid") throw std::runtime_error("Benchmark requires a complete qualified window");
        for (std::size_t i = 0; i < repeat; ++i) {
            const auto actual = analyze(data.window, data.config,backend);
            if (actual.status != result.status || actual.heart.has_value() != result.heart.has_value() ||
                (actual.heart && actual.heart->bpm != result.heart->bpm))
                throw std::runtime_error("Repeated analysis changed its result");
            repeats.push_back(actual.timing);
        }
        const auto cpu_ms = 1000.0 * (std::clock() - cpu_begin) / CLOCKS_PER_SEC;
        std::ofstream json(output);
        if (!json) throw std::runtime_error("Cannot create summary");
        summary(json, data, result, input, repeats, cpu_ms);
        json.close();
        if (!json) throw std::runtime_error("Summary write failed");
        if (!trace_path.empty()) {
            std::ofstream evidence(trace_path);
            if (!evidence) throw std::runtime_error("Cannot create trace");
            trace(evidence, result);
            evidence.close();
            if (!evidence) throw std::runtime_error("Trace write failed");
        }
        std::cout << result.status << " heart=";
        if (result.heart) std::cout << result.heart->bpm; else std::cout << "null";
        std::cout << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "vitals_offline: " << error.what() << '\n';
        return 2;
    }
}
