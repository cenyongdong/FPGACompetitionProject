cmake_minimum_required(VERSION 3.24)
project(pose_engine_timing LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)
find_package(Threads REQUIRED)
find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
set(BASELINE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/baseline")
if(NOT EXISTS "${BASELINE_DIR}/sdk_profile.hpp")
  message(FATAL_ERROR "Build the new directory exported by prepare.py")
endif()
add_executable(pose_engine_timing main.cpp
  ${BASELINE_DIR}/application_core.cpp ${BASELINE_DIR}/read_input_bridge.cpp
  ${BASELINE_DIR}/input_read_sdk.cpp ${BASELINE_DIR}/input_read_contract.cpp
  ${BASELINE_DIR}/host_cpu_adapter.cpp ${BASELINE_DIR}/preprocess.cpp
  ${BASELINE_DIR}/host_failure_evidence.cpp ${BASELINE_DIR}/failure_source_readback.cpp
  ${BASELINE_DIR}/host_stage_observation.cpp ${BASELINE_DIR}/invocation_evidence.cpp
  ${BASELINE_DIR}/producer_count_observation.cpp ${BASELINE_DIR}/tensor_identity_observation.cpp)
target_include_directories(pose_engine_timing PRIVATE ${BASELINE_DIR})
target_compile_options(pose_engine_timing PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
target_link_libraries(pose_engine_timing PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
