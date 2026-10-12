#pragma once
#include <cstddef>
#include <functional>
namespace pose::input_read {
// A pointer into an owned Host allocation. Device addresses never enter here.
struct HostView { char* data; size_t offset,capacity; };
void boundedRead(HostView destination,size_t bytes,const std::function<void(char*,size_t)>& reader);
}
