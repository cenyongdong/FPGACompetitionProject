cmake_minimum_required(VERSION 3.24)
project(pose180_pipeline LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(CORE "${PROJECT_ROOT}/software/core/display")
set(PIPE_DISPLAY "${PROJECT_ROOT}/FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display")
set(PREPROCESS "${PROJECT_ROOT}/demo_v1/shared_fp16")
include_directories(board "${PREPROCESS}" "${PROJECT_ROOT}")
add_executable(buffer_tests board/buffer_tests.cpp)
target_link_libraries(buffer_tests PRIVATE Threads::Threads)
add_executable(renderer_tests board/renderer_tests.cpp "${CORE}/hdmi_renderer.cpp"
    "${PROJECT_ROOT}/FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/joint/projection.cpp")
target_include_directories(renderer_tests PRIVATE "${CORE}")
option(POSE180_BUILD_SDK "Build the ARM64 SDK owner" OFF)
set(DEMO_SOURCES resident/main.cpp resident/io.cpp resident/journal.cpp resident/csi.cpp
    "${PROJECT_ROOT}/tools/nexmon/board/ingress.cpp" "${PROJECT_ROOT}/tools/nexmon/board/pcap_stream.cpp"
    "${PREPROCESS}/preprocess.cpp")
if(UNIX)
    add_executable(pose180_demo_mock ${DEMO_SOURCES})
    target_include_directories(pose180_demo_mock PRIVATE "${PROJECT_ROOT}/tools/nexmon/board")
    target_compile_options(pose180_demo_mock PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
    target_link_libraries(pose180_demo_mock PRIVATE Threads::Threads)
endif()
if(POSE180_BUILD_SDK)
    find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
    find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
    add_executable(pose180_pipeline board/main.cpp board/runtime.cpp "${PREPROCESS}/preprocess.cpp"
        "${CORE}/hdmi_renderer.cpp"
        "${PROJECT_ROOT}/FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/joint/projection.cpp"
        "${PIPE_DISPLAY}/hdmi_output.cpp")
    target_include_directories(pose180_pipeline BEFORE PRIVATE "${PIPE_DISPLAY}")
    target_include_directories(pose180_pipeline PRIVATE "${CORE}"
        "${PROJECT_ROOT}/demo_v1/board" "${PROJECT_ROOT}/FPGA/hdmi_candidate/software")
    target_compile_options(pose180_pipeline PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
    target_link_options(pose180_pipeline PRIVATE -Wl,--no-as-needed)
    target_link_libraries(pose180_pipeline PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
    add_executable(pose180_demo ${DEMO_SOURCES} board/runtime.cpp "${CORE}/hdmi_renderer.cpp"
        "${PROJECT_ROOT}/FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/joint/projection.cpp"
        "${PIPE_DISPLAY}/hdmi_output.cpp")
    target_compile_definitions(pose180_demo PRIVATE POSE180_DEMO_SDK=1)
    target_include_directories(pose180_demo BEFORE PRIVATE "${PIPE_DISPLAY}")
    target_include_directories(pose180_demo PRIVATE "${CORE}" "${PROJECT_ROOT}/demo_v1/board"
        "${PROJECT_ROOT}/FPGA/hdmi_candidate/software" "${PROJECT_ROOT}/tools/nexmon/board")
    target_compile_options(pose180_demo PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
    target_link_options(pose180_demo PRIVATE -Wl,--no-as-needed)
    target_link_libraries(pose180_demo PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
endif()
