cmake_minimum_required(VERSION 3.24)
project(wifi_pose_demo LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)
find_package(Threads REQUIRED)
find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
if(NOT BASELINE_DIR OR NOT VENDOR_DIR)
  message(FATAL_ERROR "Use build.py to verify/export baseline aliases and vendor identity")
endif()
add_library(demo_runtime STATIC
  ${BASELINE_DIR}/application_core.cpp ${BASELINE_DIR}/read_input_bridge.cpp
  ${BASELINE_DIR}/input_read_sdk.cpp ${BASELINE_DIR}/input_read_contract.cpp
  ${BASELINE_DIR}/host_cpu_adapter.cpp ${BASELINE_DIR}/preprocess.cpp
  ${BASELINE_DIR}/host_failure_evidence.cpp ${BASELINE_DIR}/failure_source_readback.cpp
  ${BASELINE_DIR}/host_stage_observation.cpp ${BASELINE_DIR}/invocation_evidence.cpp
  ${BASELINE_DIR}/producer_count_observation.cpp ${BASELINE_DIR}/tensor_identity_observation.cpp)
target_include_directories(demo_runtime PUBLIC ${BASELINE_DIR})
target_link_libraries(demo_runtime PUBLIC Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(demo_runtime PRIVATE -ffp-contract=off)
add_executable(pose_demo board/main.cpp board/demo_video.cpp board/demo_results.cpp board/demo_engine.cpp
  ${BASELINE_DIR}/tcp_receiver.cpp ${BASELINE_DIR}/display_process.cpp ${BASELINE_DIR}/display_protocol.cpp
  ${BASELINE_DIR}/skeleton_render.cpp ${BASELINE_DIR}/timed_resident_encoder.cpp
  ${BASELINE_DIR}/h264_access_unit.cpp ${BASELINE_DIR}/access_unit_channel.cpp ${BASELINE_DIR}/timed_guarded_rtsp.cpp)
target_include_directories(pose_demo PRIVATE board ${BASELINE_DIR} ${VENDOR_DIR}
  ${VENDOR_DIR}/live/liveMedia/include ${VENDOR_DIR}/live/UsageEnvironment/include
  ${VENDOR_DIR}/live/BasicUsageEnvironment/include ${VENDOR_DIR}/live/groupsock/include)
target_link_libraries(pose_demo PRIVATE demo_runtime -Wl,--start-group
  ${VENDOR_DIR}/libs/libliveMedia.a ${VENDOR_DIR}/libs/libgroupsock.a
  ${VENDOR_DIR}/libs/libBasicUsageEnvironment.a ${VENDOR_DIR}/libs/libUsageEnvironment.a
  ${VENDOR_DIR}/libs/libssl.a ${VENDOR_DIR}/libs/libcrypto.a -Wl,--end-group dl Threads::Threads)
target_compile_options(pose_demo PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_display_worker ${BASELINE_DIR}/display_worker.cpp ${BASELINE_DIR}/display_protocol.cpp ${BASELINE_DIR}/skeleton_render.cpp)
target_include_directories(pose_display_worker PRIVATE ${BASELINE_DIR})
target_compile_options(pose_display_worker PRIVATE -ffp-contract=off)
add_executable(pose_demo_transport_test ${BASELINE_DIR}/tcp_transport_check.cpp ${BASELINE_DIR}/tcp_receiver.cpp)
target_include_directories(pose_demo_transport_test PRIVATE ${BASELINE_DIR})
target_link_libraries(pose_demo_transport_test PRIVATE Threads::Threads)
