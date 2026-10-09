"""Isolated error-only SDK source reads; accepted and failed sources stay frozen."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as old
root=old.ROOT
def put(rel,text):
    p=root/rel;assert not p.exists(),p;p.write_text(text,encoding='utf-8',newline='\n')
bridge=(root/'software/pose_v1/src/trace_application_bridge_r2.cpp').read_text(encoding='utf-8').replace('#include "host_failure_evidence.hpp"','#include "host_failure_evidence.hpp"\n#include "failure_source_readback.hpp"')
needle="declarations<<']';pose::failure_evidence::save(frame_id,invocation_id,op->op_id,error.what(),blobs,declarations.str());";assert bridge.count(needle)==1
bridge=bridge.replace(needle,needle+'\n            size_t totalBytes=0;for(const auto& b:blobs)totalBytes+=b.bytes.size();\n            pose::source_diagnostic::capture(frame_id,invocation_id,op->op_id,inputs,allowed_device,permit_hardware,totalBytes);')
put('software/pose_v1/src/source_application_bridge_r4.cpp',bridge)
entry=(root/'software/pose_v1/src/forward_trace_check_r2.cpp').read_text(encoding='utf-8').replace('#include "host_failure_evidence.hpp"','#include "host_failure_evidence.hpp"\n#include "failure_source_readback.hpp"')
needle='pose::failure_evidence::configure(out/"failed-host-inputs");';assert entry.count(needle)==1
put('software/pose_v1/src/source_readback_check_r4.cpp',entry.replace(needle,needle+'\n        pose::source_diagnostic::configure(out/"failed-host-inputs/source-readback");'))
probe=(root/'software/pose_v1/src/host_failure_adapter_test_r3.cpp').read_text(encoding='utf-8').replace('#include "host_failure_evidence.hpp"','#include "host_failure_evidence.hpp"\n#include "failure_source_readback.hpp"')
probe=probe.replace('pose::failure_evidence::configure(out/"failed-host-inputs");','pose::failure_evidence::configure(out/"failed-host-inputs");\n    pose::source_diagnostic::configure(out/"failed-host-inputs/source-readback");')
needle='if(std::filesystem::exists(out/"failed-host-inputs/capture-error.txt"))';assert probe.count(needle)==1
extra='''for(size_t round=0;round<2;++round)for(size_t i=0;i<inputs.size();++i){
        std::vector<char> blob(values[i].size()*4);const auto file="round"+std::to_string(round)+".input"+std::to_string(i)+".f32";
        std::ifstream source(out/"failed-host-inputs/source-readback"/file,std::ios::binary);source.read(blob.data(),std::streamsize(blob.size()));
        if(!source||std::memcmp(blob.data(),values[i].data(),blob.size())!=0)throw std::runtime_error("Host source readback bytes differ");
    }
    '''
put('software/pose_v1/src/source_failure_adapter_test_r4.cpp',probe.replace(needle,extra+needle))
cm=(root/'tools/pose-v1/forward-trace-r2-CMakeLists.txt').read_text(encoding='utf-8').replace('host_failure_evidence.cpp host_failure_adapter_test.cpp','host_failure_evidence.cpp host_failure_adapter_test.cpp failure_source_readback.cpp')
put('tools/pose-v1/source-readback-r4-CMakeLists.txt',cm)
put('tools/pose-v1/Build-SourceReadbackR4.ps1',(root/'tools/pose-v1/Build-ForwardTraceR3.ps1').read_text(encoding='utf-8').replace('mixed-20261009-forward-trace-r3','mixed-20261009-source-readback-r4'))
put('tools/pose-v1/run-source-readback-r4.sh',(root/'tools/pose-v1/run-forward-trace-r3.sh').read_text(encoding='utf-8'))
review=(root/'tools/pose-v1/review_forward_r3_stage.py').read_text(encoding='utf-8').replace('Build-ForwardTraceR3.ps1','Build-SourceReadbackR4.ps1').replace('run-forward-trace-r3.sh','run-source-readback-r4.sh').replace("'trace_r3_frozen_sources')","'trace_r3_frozen_sources','source_r4_frozen_sources')")
needle="assert not (out/'failed-host-inputs/capture-error.txt').exists()";assert review.count(needle)==1
extra='''
            reads=load(out/'failed-host-inputs/source-readback/readback.json');assert reads['rounds']==2 and reads['single_round_bytes']==47040 and reads['method']=='Tensor::read'
            assert not reads['direct_device_dereference'] and not reads['explicit_wait_or_reset']
            for source in reads['sources']:
                assert not source['device'] and source['pointer']=='CPTR' and source['address']==0 and source['offset']+source['bytes']<=source['chunk_bytes']
                for rr in source['reads']:
                    assert rr['begin_ns']<=rr['end_ns'] and (out/'failed-host-inputs/source-readback'/rr['file']).read_bytes()==(out/'failed-host-inputs'/('input'+str(source['slot'])+'.f32')).read_bytes()
'''
put('tools/pose-v1/review_source_r4_stage.py',review.replace(needle,needle+extra))
base=root/'.local/pose-v1-forward-trace/package-20261009-r3';old.verify(base);m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
mapping={
'software/pose_v1/src/trace_application_bridge_r2.cpp':'software/pose_v1/src/source_application_bridge_r4.cpp',
'software/pose_v1/src/forward_trace_check_r2.cpp':'software/pose_v1/src/source_readback_check_r4.cpp',
'software/pose_v1/src/host_failure_adapter_test_r3.cpp':'software/pose_v1/src/source_failure_adapter_test_r4.cpp',
'tools/pose-v1/forward-trace-r2-CMakeLists.txt':'tools/pose-v1/source-readback-r4-CMakeLists.txt'}
m['source_r4_frozen_sources']={rel:old.sha(root/rel) for rel in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=old.sha(root/after))
for rel in ('include/failure_source_readback.hpp','src/failure_source_readback.cpp'):
    source='software/pose_v1/'+rel;m['build_files'][source]=dict(destination=Path(rel).name,sha256=old.sha(root/source))
for name in ('prepare_source_readback_r4.py','Build-SourceReadbackR4.ps1','run-source-readback-r4.sh','review_source_r4_stage.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
m['build_script']='tools/pose-v1/Build-SourceReadbackR4.ps1';m['source_readback']=dict(error_only=True,rounds=2,method='Tensor::read',max_single_round_bytes='original staged input bytes',direct_ADDR_dereference=False,wait_reset_cache=False)
out=root/'.local/pose-v1-source-readback/package-20261009-r4';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(old.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(json.dumps(dict(payloads=old.verify(out),build_sources=len(m['build_files']))))
