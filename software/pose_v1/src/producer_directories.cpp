#include "producer_directories.hpp"
#include <chrono>
#include <fstream>
#include <stdexcept>
#include <sstream>

namespace pose::producer_directories {
namespace {
namespace fs = std::filesystem;
void require(bool b, const char* s) { if (!b) throw std::runtime_error(s); }
uint64_t now() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}
bool absent(const fs::path& p) {
    std::error_code e;
    const auto s = fs::symlink_status(p, e);
    require(!e || e == std::errc::no_such_file_or_directory,
            "Directory status failed");
    return s.type() == fs::file_type::not_found;
}
std::string quote(const std::string& s) {
    std::ostringstream out; out << '"';
    for (const unsigned char c : s) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) throw std::runtime_error("Control byte in directory path");
        else out << c;
    }
    out << '"'; return out.str();
}
void save(const fs::path& p, const std::string& s) {
    require(absent(p), "Preserve directory evidence");
    std::ofstream f(p, std::ios::binary); f << s; f.close();
    require(bool(f), "Directory evidence write failed");
}
}
PreparedDirectories::PreparedDirectories(const fs::path& freshRoot)
    : owner_(std::this_thread::get_id()) {
    require(!freshRoot.empty(), "Empty directory root");
    for (const auto& part : freshRoot)
        require(part != ".." && part != ".", "Unnormalized directory root");
    root_ = fs::absolute(freshRoot).lexically_normal();
    require(root_ != root_.root_path(), "Filesystem root is not evidence root");
    fs::path ancestor = root_.root_path();
    for (const auto& part : root_.parent_path().relative_path()) {
        ancestor /= part;
        const auto status = fs::symlink_status(ancestor);
        require(fs::is_directory(status) && !fs::is_symlink(status),
                "Evidence ancestor must be a real directory");
    }
    require(absent(root_), "Evidence root must be new and exclusive");
    require(fs::create_directory(root_), "Exclusive evidence root creation failed");
}
void PreparedDirectories::owner() const {
    require(owner_ == std::this_thread::get_id(), "Directory owner thread differs");
}
void PreparedDirectories::prepare(unsigned count) {
    owner(); require(!attempted_, "Directory preparation is one-use");
    attempted_ = true;
    require(count == 4 || count == 100, "Only four or100 directories supported");
    begin_ = now();
    require(fs::is_directory(fs::symlink_status(root_)) &&
            !fs::is_symlink(fs::symlink_status(root_)), "Evidence root changed");
    require(absent(root_/"directories.prepared.json") &&
            absent(root_/"directories.summary.json"), "Old directory evidence");
    // Verify all destination paths before creating any. Other root evidence is
    // owned by this process (SDK initialization and memory round trips).
    paths_.reserve(count);
    for (unsigned i = 0; i < count; ++i) {
        auto p = root_/("call-"+std::to_string(i));
        require(p.parent_path() == root_ && absent(p), "Call path already exists");
        paths_.push_back(std::move(p));
    }
    for (const auto& p : paths_) {
        require(fs::create_directory(p), "Call directory creation failed");
        require(fs::is_directory(fs::symlink_status(p)) && fs::is_empty(p),
                "Prepared call must be an empty real directory");
    }
    end_ = now();
    std::ostringstream doc;
    doc << "{\"root\":" << quote(root_.generic_string())
        << ",\"count\":" << count << ",\"begin_ns\":" << begin_
        << ",\"end_ns\":" << end_ << ",\"exclusive_root\":true,"
           "\"empty_at_preparation\":true,\"hot_filesystem_calls\":0,\"calls\":[";
    for (unsigned i = 0; i < count; ++i) {
        if (i) doc << ',';
        doc << quote(paths_[i].generic_string());
    }
    doc << "]}\n"; save(root_/"directories.prepared.json", doc.str());
    prepared_ = true;
}
fs::path PreparedDirectories::consume(unsigned invocation) {
    owner(); require(prepared_, "Directories not prepared");
    require(invocation == consumed_, "Directory token out of order or reused");
    require(consumed_ < paths_.size(), "Directory capacity exceeded");
    auto ownedPath = paths_[consumed_]; ++consumed_; return ownedPath;
}
void PreparedDirectories::saveSummary() const {
    owner();
    save(root_/"directories.summary.json", "{\"prepared\":"+
         std::string(prepared_ ? "true" : "false")+",\"count\":"+
         std::to_string(paths_.size())+",\"consumed\":"+
         std::to_string(consumed_)+",\"hot_filesystem_calls\":0}\n");
}
}
