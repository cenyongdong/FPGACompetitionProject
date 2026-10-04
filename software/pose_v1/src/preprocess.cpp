#include "preprocess.hpp"
#include <cmath>
#include <cstring>
#include <fstream>
#include <stdexcept>

namespace pose_v1 {
namespace {
constexpr double pi = 3.141592653589793238462643383279502884;
constexpr double period = 2.0 * pi;
using CarrierPhase = std::array<double, kCarriers>;
CarrierPhase unwrap(const CarrierPhase& values) {
    CarrierPhase result{};
    result[0] = values[0];
    double correction = 0.0;
    for (std::size_t n = 1; n < kCarriers; ++n) {
        const double delta = values[n] - values[n-1];
        double adjusted = std::fmod(delta + pi, period);
        if (adjusted < 0) adjusted += period;
        adjusted -= pi;
        if (adjusted == -pi && delta > 0) adjusted = pi;
        if (std::abs(delta) >= pi) correction += adjusted - delta;
        result[n] = values[n] + correction;
    }
    return result;
}
std::uint64_t read_le(std::istream& stream, std::size_t bytes) {
    std::uint64_t result = 0;
    for (std::size_t i=0; i<bytes; ++i) {
        const int c = stream.get();
        if (c == EOF) throw std::runtime_error("Truncated window header");
        result |= std::uint64_t(static_cast<unsigned char>(c)) << (8*i);
    }
    return result;
}
double read_double(std::istream& stream) {
    auto bits = read_le(stream, 8);
    double value;
    static_assert(sizeof(value) == sizeof(bits), "IEEE float64 required");
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}
}

Tokens preprocess(const RawCsi& csi) {
    for (const auto& value : csi) {
        if (!std::isfinite(value.real()) || !std::isfinite(value.imag()))
            throw std::runtime_error("Non-finite raw CSI");
    }
    Tokens output{};
    // Training db11 has filter length 22, with only 20 time samples:
    // wavedec's maximum level is 0, so waverec returns abs(csi) unchanged.
    constexpr double step = 2.0 * pi * 625.0;
    double A=0, B=0, C=0;
    for (std::size_t a=0; a<kAntennas; ++a)
        for (std::size_t n=0; n<kCarriers; ++n) {
            const double x = step * n;
            A += x*x; B += x; C += 1.0;
        }
    for (std::size_t r=0; r<kReceivers; ++r) {
        for (std::size_t t=0; t<kTimes; ++t) {
            std::array<CarrierPhase, kAntennas> phase{};
            CarrierPhase initial{};
            for (std::size_t n=0; n<kCarriers; ++n)
                initial[n] = std::arg(csi[raw_index(r, 0, n, t)]);
            phase[0] = unwrap(initial);
            for (std::size_t a=1; a<kAntennas; ++a) {
                for (std::size_t n=0; n<kCarriers; ++n) {
                    const auto now = csi[raw_index(r,a,n,t)];
                    const auto before = csi[raw_index(r,a-1,n,t)];
                    initial[n] = phase[a-1][n] + std::arg(now * std::conj(before));
                }
                phase[a] = unwrap(initial);
            }
            double D=0, E=0;
            for (std::size_t a=0; a<kAntennas; ++a)
                for (std::size_t n=0; n<kCarriers; ++n) {
                    D += step * n * phase[a][n]; E += phase[a][n];
                }
            const double denominator = A*C - B*B;
            const double rho = (B*E - C*D) / denominator;
            const double beta = (B*D - A*E) / denominator;
            for (std::size_t a=0; a<kAntennas; ++a)
                for (std::size_t n=0; n<kCarriers; ++n) {
                    const double magnitude = std::abs(csi[raw_index(r,a,n,t)]);
                    const double corrected = phase[a][n] + step*n*rho + beta;
                    // Training multiplies a real amplitude by a complex exponential.
                    // Preserve both complex components' signed-zero arithmetic:
                    // replacing this with atan2(m*sin(phi),m*cos(phi)) is different
                    // for zero-amplitude bins present in the actual dataset.
                    const auto reconstructed = std::complex<double>(magnitude,0.0)
                                             * std::exp(std::complex<double>(0.0,corrected));
                    const double wrapped = std::arg(reconstructed);
                    const auto offset = ((r*kAntennas+a)*kTimes+t)*60;
                    output[offset+n] = static_cast<float>(magnitude);
                    output[offset+30+n] = static_cast<float>(wrapped);
                }
        }
    }
    for (float value : output)
        if (!std::isfinite(value)) throw std::runtime_error("Non-finite model input");
    return output;
}

Window read_window(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) throw std::runtime_error("Cannot open CSI window");
    char magic[8]{};
    file.read(magic, 8);
    if (!file || std::memcmp(magic, "PIWCSI1\0", 8) != 0)
        throw std::runtime_error("Invalid CSI window magic");
    if (read_le(file,4) != 1 || read_le(file,4) != kPayloadBytes)
        throw std::runtime_error("Unsupported CSI version or payload size");
    Window result;
    result.frame_id = read_le(file,8);
    result.source_time_ns = read_le(file,8);
    for (auto& value : result.csi) {
        const double re = read_double(file), im = read_double(file);
        value = {re,im};
    }
    if (file.peek() != EOF) throw std::runtime_error("Trailing data after single window");
    return result;
}

void write_tokens(const std::string& filename, const Tokens& tokens) {
    std::ofstream file(filename, std::ios::binary | std::ios::trunc);
    if (!file) throw std::runtime_error("Cannot open output tensor");
    for (float value : tokens) {
        std::uint32_t bits;
        std::memcpy(&bits, &value, sizeof(bits));
        for (int b=0; b<4; ++b) file.put(static_cast<char>((bits >> (8*b)) & 255));
    }
    if (!file) throw std::runtime_error("Tensor write failed");
}
}
