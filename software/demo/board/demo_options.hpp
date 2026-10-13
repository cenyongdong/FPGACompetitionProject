// 命令行解析：仅校验参数并返回拥有值，不访问设备、网络或文件系统。
#pragma once

#include <filesystem>
#include <string>

namespace wifi_demo {

struct Options {
    std::filesystem::path model;
    std::filesystem::path output;
    std::string bind;
    unsigned long maximum;
    unsigned long input_port;
    unsigned long rtsp_port;
};

// 沿用原入口的校验顺序、默认值和异常文本；由main捕获解析异常。
Options parseOptions(int argc, char** argv);

} // namespace wifi_demo
