#include "producer_directories.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <functional>
#include <exception>
namespace {
namespace fs = std::filesystem;
void require(bool b) { if (!b) throw std::runtime_error("Directory contract failed"); }
unsigned rejected = 0;
void reject(const std::function<void()>& f) {
    bool failed = false;
    try { f(); } catch (const std::exception&) { failed = true; }
    require(failed); ++rejected;
}
}
int main(int argc, char** argv) {
    using pose::producer_directories::PreparedDirectories;
    try {
        require(argc == 2); const fs::path root = argv[1];
        require(!fs::exists(root)); require(fs::create_directory(root));
        reject([&]{ PreparedDirectories p(root); });
        reject([&]{ PreparedDirectories p(root/".."/"traversal"); });
        reject([&]{ PreparedDirectories p(fs::path{}); });
        { std::ofstream f(root/"file"); f << "old"; }
        reject([&]{ PreparedDirectories p(root/"file"); });
        fs::create_directory_symlink(root, root/"link");
        reject([&]{ PreparedDirectories p(root/"link"); });
        reject([&]{ PreparedDirectories p(root/"link"/"ancestor"); });
        PreparedDirectories invalid(root/"invalid");
        reject([&]{ invalid.prepare(101); });
        reject([&]{ invalid.prepare(4); });
        reject([&]{ invalid.consume(0); });
        PreparedDirectories collision(root/"collision");
        { std::ofstream f(root/"collision/call-2"); f << "old"; }
        reject([&]{ collision.prepare(4); });
        require(!fs::exists(root/"collision/call-0"));
        for (const unsigned count : {4U,100U}) {
            const auto base = root/("valid-"+std::to_string(count));
            PreparedDirectories p(base);
            { std::ofstream f(base/"sdk-evidence.json"); f << "{}\n"; }
            p.prepare(count);
            for (unsigned i = 0; i < count; ++i)
                require(fs::is_directory(base/("call-"+std::to_string(i))) &&
                        fs::is_empty(base/("call-"+std::to_string(i))));
            reject([&]{ p.prepare(count); });
            reject([&]{ p.consume(1); });
            std::exception_ptr threadError;
            std::thread t([&]{try { p.consume(0); } catch (...) {threadError=std::current_exception();}});
            t.join(); require(bool(threadError)); ++rejected;
            for (unsigned i = 0; i < count; ++i) {
                const auto owned = p.consume(i); require(owned == fs::absolute(base/("call-"+std::to_string(i))));
                { std::ofstream f(owned/"output.bin",std::ios::binary); f << "owned-output"; f.close(); require(bool(f)); }
                std::ifstream f(owned/"output.bin",std::ios::binary);
                std::string s; std::getline(f,s); require(s=="owned-output");
                reject([&]{ p.consume(i); });
            }
            reject([&]{ p.consume(count); });
            p.saveSummary(); reject([&]{ p.saveSummary(); });
            reject([&]{ PreparedDirectories duplicate(base); });
        }
        std::cout << "Prepared directories: four/100 unique empty paths, sequential owned tokens, "
                  << rejected << " rejections, thread/ownership/save compatibility passed; no SDK\n";
        return 0;
    } catch(const std::exception& e) {std::cerr << e.what() << '\n'; return 1;}
}
