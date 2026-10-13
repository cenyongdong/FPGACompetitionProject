#include "demo_options.hpp"

#include <map>
#include <stdexcept>

namespace wifi_demo {

namespace {

void need(bool valid, const char* message) {
    if (!valid) {
        throw std::runtime_error(message);
    }
}

} // namespace

Options parseOptions(int argc, char** argv) {
    // 1. 按原顺序读取参数，拒绝重复名称和缺失的参数值。
    std::map<std::string, std::string> options;
    for (int i = 1; i < argc; ++i) {
        std::string name = argv[i];
        need(!options.count(name), "Duplicate demo option");

        if (name == "--allow-device-init" || name == "--allow-vpu-stream" || name == "--allow-network") {
            options[name] = "yes";
        } else {
            need(i + 1 < argc, "Missing demo option value");
            options[name] = argv[++i];
        }
    }

    // 2. 显式设备标志仍是必须参数，目录和端口的契约不改变。
    for (const auto& item : options) {
        need(item.first == "--model-dir" || item.first == "--output" || item.first == "--bind" ||
             item.first == "--input-port" || item.first == "--rtsp-port" || item.first == "--max-frames" ||
             item.first == "--allow-device-init" || item.first == "--allow-vpu-stream" ||
             item.first == "--allow-network", "Unknown demo option");
    }
    need(options.count("--model-dir") && options.count("--output") &&
         options.count("--allow-device-init") && options.count("--allow-vpu-stream") &&
         options.count("--allow-network"), "Model/output and three explicit hardware flags required");

    auto get = [&](const char* name, const char* fallback) {
        return options.count(name) ? options.at(name) : std::string(fallback);
    };
    auto number = [&](const char* name, const char* fallback) {
        auto value = get(name, fallback);
        need(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
             "Invalid unsigned demo option");
        return std::stoul(value);
    };

    // 3. 保持原数值转换顺序，失败发生在任何资源初始化之前。
    const auto maximum = number("--max-frames", "60");
    const auto port = number("--input-port", "39001");
    const auto rtsp = number("--rtsp-port", "8554");
    need(maximum >= 1 && maximum <= 100 && port >= 1024 && port <= 65535 &&
         rtsp >= 1024 && rtsp <= 65535 && port != rtsp, "Demo option bounds differ");

    return {options.at("--model-dir"), options.at("--output"), get("--bind", "192.168.126.49"),
            maximum, port, rtsp};
}

} // namespace wifi_demo
