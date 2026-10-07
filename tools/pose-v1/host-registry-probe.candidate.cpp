// Candidate only: CPU backend registration queries, no Session or device access.
#include <icraft-xir/core/network.h>
#include <icraft-backends/hostbackend/backend.h>
#include <exception>
#include <iomanip>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>

using icraft::xir::Network;
using icraft::xrt::HostBackend;

static void inspect(const char* name, const char* path, const std::set<int64_t>& ids) {
    auto graph = Network::CreateFromJsonFile(path);
    auto backend = HostBackend::Init();
    std::set<int64_t> seen;
    for (const auto& op : graph->ops) {
        if (!ids.count(op->op_id)) continue;
        seen.insert(op->op_id);
        std::cout << "{\"graph\":" << std::quoted(name)
                  << ",\"op_id\":" << op->op_id
                  << ",\"type_key\":" << std::quoted(std::string(op->typeKey()))
                  << ",\"supported\":" << (backend.isOpSupported(op) ? "true" : "false")
                  << ",\"init_registered\":" << (backend.getInitFunc(op).has_value() ? "true" : "false")
                  << ",\"forward_registered\":" << (backend.getForwardFunc(op).has_value() ? "true" : "false")
                  << "}\n";
    }
    if (seen != ids) throw std::runtime_error("Selected operator IDs missing from graph");
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("Usage: host_registry_probe OPTIMIZED_JSON ZG_JSON");
        inspect("optimized", argv[1], {1});
        inspect("ZG_host", argv[2], {188, 192, 437, 442, 582, 649});
        std::cout << "{\"stage\":\"registration_queries_completed_no_inference\",\"device_opened\":false}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "STOP: " << error.what() << '\n';
        return 1;
    }
}
