#pragma once
#include "application_core.hpp"
#include <fstream>
#include <vector>

namespace pose::validation {
struct FixtureWindow {
    std::string name;
    pose_v1::Window window;
    pose_v1::Tokens input;
    std::array<float,100> scores;
    std::array<float,4200> poses;
};
// Diagnostic replay source and complete result oracle. Never changes the Engine.
std::vector<FixtureWindow> fixtureWindows(const std::filesystem::path&,bool expanded);
void saveVerifiedResult(const FixtureWindow&,const pose_v1::application::Result&,
                        size_t call,const std::filesystem::path&,std::ofstream&);
void persistBytes(const std::filesystem::path&,const void*,size_t);
int validatedHostGate(const std::filesystem::path& package,const std::filesystem::path& output);
}
