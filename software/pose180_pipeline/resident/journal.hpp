#pragma once
#include "core.hpp"
#include <filesystem>
#include <streambuf>
#include <sys/types.h>

namespace pose180_demo {
// Spawned before any SDK handle/thread. Only this child performs normal disk IO.
// Nonblocking atomic datagrams drop whole records under disk stalls/fullness.
class Journal : public std::streambuf {
    Shared& shared_;
    int fd_=-1;pid_t child_=-1;
    std::array<Record,8> ring_{};
    std::size_t next_=0,count_=0;
    std::array<char,2048> line_{};
    void send(unsigned char type,const void*,std::size_t);
    int sync() override;
    int_type overflow(int_type) override;
public:
    Journal(Shared&,const std::filesystem::path&);
    ~Journal();
    void record(const Record&);
    void freeze();
    void status(const std::string&);
    void diagnostic(const std::string&); // separate bounded CSI history
    pid_t child_pid() const { return child_; }
};
}
