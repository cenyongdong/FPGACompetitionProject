#pragma once
#include <array>
#include <cstdint>
#include <vector>

namespace pose_v1::render {
constexpr int width=1280,height=720;
constexpr std::array<std::array<int,2>,14> bones{{{0,1},{0,2},{0,3},{2,4},{2,5},{3,6},{3,7},{4,8},{5,7},{5,9},{6,10},{7,11},{9,12},{11,13}}};
enum class Status { Result, NoInput, Stopped };
struct Frame {
    std::vector<uint8_t> rgb;
    std::array<std::array<double,2>,14> projected{};
    std::array<float,42> selected_raw{};
    size_t top_index=0,clipped_joints=0;
    uint64_t frame_id=0;
    float score=0;
    double render_ms=0;
};
// Fixed orthographic display only: raw centre(1.75,1.75,3.4), yaw30deg,
// elevation20deg, display C2 negated, scale220 pixels/model-unit. No auto-fit.
std::array<double,2> project(double c0,double c1,double c2);
Frame draw(const std::array<float,100>& scores,const std::array<float,4200>& poses,uint64_t frame_id,Status status=Status::Result);
std::vector<uint8_t> rgb565_le(const std::vector<uint8_t>& rgb,int w,int h);
// Contiguous Y + interleaved UV/VU, BT.601 limited-range integer matrix;
// 2x2 rounded RGB box average for chroma, stride=w. Hardware negotiation pending.
std::vector<uint8_t> yuv420sp(const std::vector<uint8_t>& rgb,int w,int h,bool nv21);
}
