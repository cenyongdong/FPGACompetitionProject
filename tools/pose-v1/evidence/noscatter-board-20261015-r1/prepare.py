"""Generate a separately built model-specific engine from frozen reviewed sources.

Algorithms remain the same SDK TopK/GatherElements kernels and CSI preprocessing.
Only the new model contract and removal of Scatter-specific paths are changed.
The formal demo, old deployed graph and frozen timing evidence remain untouched.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(r'D:\FPGACompetitionProject')
E = ROOT / 'tools/pose-v1/evidence/noscatter-board-20261015-r1'
SRC = ROOT / '.local/noscatter-source-20261015-r1'
PKG = ROOT / '.local/noscatter-delivery-20261015-r1'
OLD = ROOT / '.local/engine-timing-source-20261013-r2'
OLD_PKG = ROOT / '.local/engine-timing-delivery-20261013-r3'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def put(p, s):
    p.write_bytes(s.encode('utf-8'))

def replace(s, old, new, count=1):
    assert s.count(old) == count, repr(old)
    return s.replace(old,new)

def remove_block(s, marker):
    start = s.index(marker)
    opening = s.index('{',start)
    depth = 1
    end = opening+1
    while depth:
        if s[end] == '{': depth += 1
        elif s[end] == '}': depth -= 1
        end += 1
    return s[:start]+s[end:]

assert not SRC.exists() and not PKG.exists()
shutil.copytree(OLD,SRC)
PKG.mkdir()
shutil.copytree(OLD_PKG / 'fixtures',PKG / 'fixtures')
(PKG / 'models').mkdir()
asset = ROOT / 'model/piw24_noscatter-20261014-r3'
pins={'piw24_noscatter_ZG.json':'0720b375edb7fddd7ee6f074be0e8fd0852592ae1fcbe600762525f276139ce5',
      'piw24_noscatter_ZG.raw':'29dce9c1bd1fc940cdd1364d148353227d01ec0cef82861f7d2c9045e12ee1ce'}
for name,digest in pins.items():
    assert sha(asset/name) == digest
    shutil.copyfile(asset/name,PKG/'models'/name)

profile='''// Model-specific runtime contract. Filled only after complete SDK fusion validation.
#pragma once
#include <map>
#include <set>
#include <vector>
#include <utility>
#include <cstdint>
namespace pose_v1::fusion_baseline {
    inline const std::set<int64_t> host_ids = {0,188,192,437,442,664};
    inline std::map<int64_t,std::vector<int64_t>> members;
    inline std::map<int64_t,std::pair<int,int>> sync;
    inline uint32_t final_count = 0;
}
'''
put(SRC/'baseline/mixed_fusion_baseline.hpp',profile)

p=SRC/'baseline/host_cpu_adapter.cpp'; s=p.read_text(encoding='utf-8')
s=s.replace('(Scatter indices: ***C)','')
start=s.index('        } else if (op.is < xir::ScatterND>()) {')
end=s.index('        } else throw Rejection',start)
s=s[:start]+s[end:]
s=s.replace('Only TopK/GatherElements/ScatterND are registered','Only TopK/GatherElements are registered')
s=s.replace('{ 188, 192, 437, 582, 649 }','{ 188, 192, 437 }')
s=replace(s,'        add<xir::ScatterND>();\n','')
s=replace(s,'            status = kernel::scatterND(in[0], in[1], in[2], out[0], kernel::ScatterReduction::kNone);',
            '            throw Rejection("type", "Unsupported CPU operation");')
put(p,s)

p=SRC/'baseline/read_input_bridge.cpp'; s=p.read_text(encoding='utf-8')
s=remove_block(s,'        void observe192(')
s=re.sub(r'^\s*observe192\([^\n]+\);\n','\n',s,flags=re.M)
s=remove_block(s,'            if (permit_hardware && op->op_id == 582 && index == 0) {')
s=s.replace('{ 188, 192, 437, 582, 649 }','{ 188, 192, 437 }')
s=replace(s,'        add<xir::ScatterND>();\n','')
put(p,s)

p=SRC/'baseline/lazy_runtime_validation.hpp'; s=p.read_text(encoding='utf-8')
s=s.replace('{ 188, 192, 437, 442, 582, 649 }','{ 188, 192, 437, 442 }')
s=s.replace('hard == 1173 && host == 6','hard == 1158 && host == 4')
s=s.replace('{ 188, 192, 437, 582, 649 }','{ 188, 192, 437 }')
s=remove_block(s,'                if (op.is < xir::ScatterND>()) {')
s=replace(s,'need(count == 4,','need(count == 2,')
s=replace(s,'ops.size() == 1181 && hard.size() == 1173','ops.size() == 1164 && hard.size() == 1158')
start=s.index('    inline void validate_applied_bindings(')
end=s.index('    inline void host_content_check(',start)
s=s[:start]+(E/'fusion_validation.inc').read_text(encoding='utf-8')+s[end:]
put(p,s)

p=SRC/'baseline/application_core.cpp'; s=p.read_text(encoding='utf-8')
s=s.replace('state("after_forward", 672, out)','state("after_forward", 664, out)')
s=s.replace('state("outputs_completed", 672, out)','state("outputs_completed", 664, out)')
s=s.replace('state("after_dump", 672, out)','state("after_dump", 664, out)')
s=replace(s,'const auto last = fusion_baseline::sync.at(9191);','const auto final_count = fusion_baseline::final_count;')
s=replace(s,'uint32_t(last.first + last.second)','final_count')
s=replace(s,'zg_count == 7 && observed.size() == 7','zg_count == fusion_baseline::members.size() && observed.size() == 5')
put(p,s)

# Unsupported hardware timing is not retried: prior SDK getLayerTime data were invalid.
put(SRC/'baseline/sdk_profile.hpp','''#pragma once
#include <icraft-xrt/core/session.h>
#include <filesystem>
#include <fstream>
#include <stdexcept>
namespace pose_v1::timing_sdk {
    inline bool enabled = false;
    inline void configure(bool on) { if(on) throw std::runtime_error("Unverified SDK profiling disabled"); }
    inline void collect(const icraft::xrt::Session&,const icraft::xrt::Device&, uint64_t, uint64_t) {}
    inline void save(const std::filesystem::path& p) {
        std::ofstream(p/"sdk-profile.jsonl"); std::ofstream(p/"hardware-layers.jsonl");
    }
}
''')

p=SRC/'main.cpp'; s=p.read_text(encoding='utf-8')
s=replace(s,'mode == "baseline" || mode == "wall" || mode == "sdk"','mode == "wall"')
s=s.replace('cycles >= 1 && cycles <= 8','cycles == 1')
s=s.replace('models/piw24_ZG.json','models/piw24_noscatter_ZG.json').replace('models/piw24_ZG.raw','models/piw24_noscatter_ZG.raw')
put(p,s)
p=SRC/'CMakeLists.txt'; s=p.read_text(encoding='utf-8').replace('pose_engine_timing','pose_noscatter_timing'); put(p,s)

for name in ('host_cpu_adapter.cpp','read_input_bridge.cpp','lazy_runtime_validation.hpp','application_core.cpp'):
    text=(SRC/'baseline'/name).read_text(encoding='utf-8')
    assert not any(word in text for word in ('ScatterND','kernel::scatterND','== 582','== 649','9186','9191'))
    diff=''.join(difflib.unified_diff((OLD/'baseline'/name).read_text(encoding='utf-8').splitlines(True),
             text.splitlines(True),fromfile='frozen/'+name,tofile='noscatter/'+name))
    put(E/(name+'.diff'),diff)

shutil.copyfile(OLD_PKG/'board_application_preflight.py',PKG/'board_application_preflight.py')
s=(OLD_PKG/'board_run.py').read_text(encoding='utf-8')
s=s.replace("choices=('baseline', 'wall', 'sdk')","choices=('wall',)")
s=s.replace('if not 1 <= args.cycles <= 8:','if args.cycles != 1:')
s=s.replace("root / 'pose_engine_timing'","root / 'pose_noscatter_timing'")
s=replace(s,"previous = {'wall': 'baseline', 'sdk': 'wall'}.get(args.mode)",'previous = None')
put(PKG/'board_run.py',s)

manifest={str(p.relative_to(SRC)):sha(p) for p in sorted(SRC.rglob('*')) if p.is_file() and p.name!='source-manifest.json'}
put(SRC/'source-manifest.json',json.dumps({'status':'prepared_not_executed','files':manifest,
 'origin':str(OLD),'model_pins':pins,'ScatterND_registrations':0,'Scatter_specific_counter_wait':False,
 'formal_core_modified':False,'bounded_frames':3,'timeout_seconds':120},indent=2)+'\n')
shutil.copyfile(SRC/'source-manifest.json',E/'source-manifest.json')
print(json.dumps({'source':str(SRC),'package':str(PKG),'files':len(manifest),'status':'prepared_not_run'}))
