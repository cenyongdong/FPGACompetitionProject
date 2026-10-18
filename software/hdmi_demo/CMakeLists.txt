cmake_minimum_required(VERSION 3.24)
project(pose_hdmi_demo LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)
find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
set(B ${CMAKE_CURRENT_SOURCE_DIR}/baseline)
add_executable(pose_hdmi_demo main.cpp hdmi_output.cpp hdmi_canvas.cpp skeleton_render.cpp
  ${B}/application_core.cpp ${B}/read_input_bridge.cpp ${B}/input_read_sdk.cpp ${B}/input_read_contract.cpp
  ${B}/host_cpu_adapter.cpp ${B}/preprocess.cpp ${B}/host_failure_evidence.cpp ${B}/failure_source_readback.cpp
  ${B}/host_stage_observation.cpp ${B}/invocation_evidence.cpp ${B}/producer_count_observation.cpp
  ${B}/tensor_identity_observation.cpp)
target_include_directories(pose_hdmi_demo PRIVATE ${B} ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_options(pose_hdmi_demo PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
target_link_options(pose_hdmi_demo PRIVATE -Wl,--no-as-needed)
target_link_libraries(pose_hdmi_demo PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
