"""Reuse the accepted main/core; change only HDMI raster and startup admission."""
from pathlib import Path
import re,json
W=Path(__file__).resolve().parent;J=W/'joint';J.mkdir(exist_ok=True)
B=Path('D:/FPGACompetitionProject/.local/hp2-deferred-consume-20261024-r45/source')
source=(B/'board/main.cpp').read_text()
source=source.replace('#include "hdmi_canvas.hpp"','#include "hdmi_renderer.hpp"')
source=source.replace('#include <atomic>','#include <atomic>\n#include <csignal>')
source=source.replace('namespace dv = demo_v1;',
    'namespace { volatile std::sig_atomic_t requested_stop=0; void request_stop(int){requested_stop=1;} }\nnamespace dv = demo_v1;')
source=source.replace('    dv::Queue<Input> incoming(8);',
    '    std::signal(SIGTERM,request_stop);std::signal(SIGINT,request_stop);\n    dv::Queue<Input> incoming(8);')
source=source.replace('while (auto item = incoming.pop()) {','while (auto item = incoming.pop()) {\n            need(!requested_stop,"Requested bounded test stop");')
source=source.replace('auto rendered=pose_v1::render::draw(gated.scores,gated.poses,gated.frame_id);\n            auto pixels=pose::hdmi::canvas(rendered.rgb);',
    'auto rendered=pose::hdmi::render(gated.scores,gated.poses,gated.frame_id);\n            auto pixels=std::move(rendered.rgb565);')
source=source.replace('render_canvas_ms','render_rgb565_ms')
changes=[]
def shift(m):
    before=int(m[2]);changes.append(dict(phase=m[1],before=before,after=before-10))
    return 'observer.epoch("'+m[1]+'",'+str(before-10)+','
source=re.sub(r'observer\.epoch\("([^"]+)",(\d+),',shift,source)
assert len(changes)==4
marker='        const auto before=observer.epoch("before_Engine",4,'
assert marker in source
source=source.replace(marker,'''        std::ifstream startup_file(package/"startup-mode.txt");
        std::string startup_mode;startup_file>>startup_mode;
        need(startup_mode=="consumed" || startup_mode=="healthy", "Startup admission mode absent");
        const bool consumed_startup=startup_mode=="consumed";
        const auto before=observer.epoch("before_Engine",4,''')
source=source.replace('need(pose::r9_startup::idle_after_drain(before,true),"Abnormal before Engine: no SDK start");',
'''need(consumed_startup ? pose::r9_startup::idle_after_drain(before,false) :
             (pose::r9_startup::idle_healthy(before) && before.words[4]==0),
             "Abnormal before Engine: no SDK start");''')
source=source.replace('need(pose::r9_startup::functional_reads_complete(joint),"Incomplete/error joint read bursts after discard");',
'''if(consumed_startup)
            need(pose::r9_startup::bounded_drain_quiet(joint,true),"Consumed startup terminal changed");
        else
            need((joint.words[4]&7)==5 && ((joint.words[4]>>3)&511)==0 &&
                 !(joint.words[4]&0x0c000000u), "Untouched healthy consumer changed");
        // Hardware counters naturally wrap. Preserve their original 32-bit values;
        // compare fixed-width invariants, never invent a 64-bit total.
        need(joint.words[0]==pose::r9_startup::abi && joint.words[3]==0,
             "Joint ABI/reset history changed");
        for(unsigned c=0;c<6;++c){const unsigned at=8+16*c;
            need(joint.words[at+2]==joint.words[at] && joint.words[at+1]==joint.words[at+15] &&
                 joint.words[at+3]==0 && !(joint.words[at+12]&(1u<<31)),
                 "Joint fixed-width burst/beat or sticky error contract failed");
        }
        for(unsigned key:{0u,1u,2u})
            need(joint.words[88+key]==uint32_t(joint.words[40+key]+joint.words[72+key]),
                 "HP2 branch conservation failed modulo 2^32");''')
(J/'main.cpp').write_bytes(source.encode())
original=(B/'display/skeleton_render.cpp').read_text()
body=original[original.index('    std::array<double, 2> project('):original.index('\n    Frame draw(')]
projection='''// Original public display projection relocated without arithmetic changes.
#include "skeleton_render.hpp"
#include <cmath>
#include <stdexcept>
namespace pose_v1::render {
namespace { constexpr double pi=3.14159265358979323846;
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);} }
'''+body+'\n}\n'
(J/'projection.cpp').write_bytes(projection.encode())
cmake=(B/'CMakeLists.txt').read_text()
cmake=cmake.replace('set(B ${CMAKE_CURRENT_SOURCE_DIR}/shared_fp16)','set(B ${BASE_SOURCE}/shared_fp16)')
cmake=cmake.replace('board/main.cpp output/pose_frame.cpp','main.cpp ${BASE_SOURCE}/output/pose_frame.cpp')
cmake=cmake.replace('diagnostics/','${BASE_SOURCE}/diagnostics/')
cmake=cmake.replace('${B} board output','${B} ${BASE_SOURCE}/board ${BASE_SOURCE}/output ${BASE_SOURCE}/display ${NATIVE_SOURCE}')
cmake=cmake.replace('display/hdmi_output.cpp display/hdmi_canvas.cpp display/skeleton_render.cpp',
    '${BASE_SOURCE}/display/hdmi_output.cpp ${NATIVE_SOURCE}/hdmi_renderer.cpp projection.cpp')
cmake=cmake.replace('PRIVATE display)','PRIVATE ${BASE_SOURCE}/display ${NATIVE_SOURCE})')
cmake='''cmake_minimum_required(VERSION 3.24)
project(pose_demo_v1 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Threads REQUIRED)
find_package(icraft-hostbackend 3.39.0.0 EXACT REQUIRED)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
file(GLOB_RECURSE BASE_OBJECTS "${BASE_SOURCE}/build/CMakeFiles/pose_demo_v1.dir/*.o")
list(FILTER BASE_OBJECTS EXCLUDE REGEX "/board/main[.]cpp[.]o$|/display/(skeleton_render|hdmi_canvas)[.]cpp[.]o$")
list(LENGTH BASE_OBJECTS BASE_COUNT)
if(BASE_COUNT LESS 10)
    message(FATAL_ERROR "Accepted r45 common object checkpoint unavailable")
endif()
file(WRITE "${CMAKE_BINARY_DIR}/reused-objects.txt" "${BASE_OBJECTS}")
add_executable(pose_demo_v1 main.cpp projection.cpp ${NATIVE_SOURCE}/hdmi_renderer.cpp ${BASE_OBJECTS})
target_include_directories(pose_demo_v1 BEFORE PRIVATE ${BASE_SOURCE}/diagnostics)
target_include_directories(pose_demo_v1 PRIVATE ${BASE_SOURCE}/shared_fp16 ${BASE_SOURCE}/board
    ${BASE_SOURCE}/output ${BASE_SOURCE}/display ${NATIVE_SOURCE})
target_compile_definitions(pose_demo_v1 PRIVATE DEMO_READ_DIAGNOSTIC=1 DEMO_D47_ISOLATION=1)
target_compile_options(pose_demo_v1 PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
target_link_options(pose_demo_v1 PRIVATE -Wl,--no-as-needed)
target_link_libraries(pose_demo_v1 PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
'''
(J/'CMakeLists.txt').write_bytes(cmake.encode())
(J/'source-change.json').write_bytes((json.dumps(dict(baseline=str(B),changes=changes,
    model_math_SDK_NPU_protocol_changed=False,RGB24_intermediate_removed=True,
    upscale_removed=True,skeleton_scale_preserved=True),indent=2)+'\n').encode())
print('Prepared direct RGB565 integration; existing inference, 200ms adoption and wire protocol unchanged.')
