"""Generate auditable isolated SDK/application adapters from frozen approved sources."""
from pathlib import Path
import difflib, hashlib

R = Path(__file__).resolve().parents[2]
include = R / 'software/pose_v1/include'
src = R / 'software/pose_v1/src'
original = (src / 'producer_sdk.cpp').read_text()
assert hashlib.sha256((src / 'producer_sdk.cpp').read_bytes()).hexdigest() == 'd6ff89dda8e914045e2db7c5200971083c217ffb9f3c9c90202e1b3fdccfcdd1'

def replace(text, old, new):
    assert text.count(old) == 1, old[:120]
    return text.replace(old, new)

h = (include / 'producer_sdk.hpp').read_text().replace('SdkGroup', 'SdkPhaseGroup')
h = replace(h, '#include <memory>', '#include <memory>\n#include "producer_phase_trace.hpp"')
h = replace(h, 'size_t invocation);', 'size_t invocation,pose::producer_phase::Trace&,uint64_t planned);')
s = original.replace('SdkGroup', 'SdkPhaseGroup').replace('"producer_sdk.hpp"', '"producer_phase_sdk.hpp"')
s = replace(s, 'namespace xir=icraft::xir;', '''namespace phase=pose::producer_phase;
template<class F> decltype(auto) observed(phase::Trace* trace,phase::Phase ph,int64_t value,F&& f){
    if(trace){return trace->run(ph,value,std::forward<F>(f));}return std::forward<F>(f)();
}
namespace xir=icraft::xir;''')
s = replace(s, 'std::vector<xrt::Tensor> inputs(const Payload&p){', 'std::vector<xrt::Tensor> inputs(const Payload&p,phase::Trace* trace=nullptr){')
s = replace(s, 'auto host=xrt::Tensor(ins[i].tensorType()).mallocOn(xrt::HostDevice::MemRegion());checkStorage(host,ins[i].tensorType(),xrt::HostDevice::MemRegion());need(host.data().ptype()==xrt::PtrType::CPTR,"Host input not CPTR");', '''auto host=observed(trace,phase::Phase::HostAllocate,inputIds[i],[&]{return xrt::Tensor(ins[i].tensorType()).mallocOn(xrt::HostDevice::MemRegion());});
            observed(trace,phase::Phase::HostStorage,inputIds[i],[&]{checkStorage(host,ins[i].tensorType(),xrt::HostDevice::MemRegion());need(host.data().ptype()==xrt::PtrType::CPTR,"Host input not CPTR");});''')
s = replace(s, 'auto bytes=p.inputs[i];host.write(0,bytes.data(),bytes.size());list.push_back(host);', '''auto bytes=observed(trace,phase::Phase::InputBytes,inputIds[i],[&]{return p.inputs[i];});
            observed(trace,phase::Phase::HostWrite,inputIds[i],[&]{host.write(0,bytes.data(),bytes.size());});list.push_back(host);''')
s = replace(s, 'size_t invocation){', 'size_t invocation,phase::Trace& trace,uint64_t planned){')
s = replace(s, 'p_->check();need(!p_->mock,"Never forward on mock");validate(p);auto inputs=p_->inputs(p);', '''trace.run(phase::Phase::OwnerCheck,-1,[&]{p_->check();need(!p_->mock,"Never forward on mock");});
    trace.run(phase::Phase::Validate,-1,[&]{validate(p);});auto inputs=p_->inputs(p,&trace);''')
s = replace(s, 'std::ofstream journal(out/"stages.jsonl");need(bool(journal),"Cannot save per-call stages");', '''std::ofstream journal;trace.run(phase::Phase::JournalOpen,-1,[&]{journal.open(out/"stages.jsonl");need(bool(journal),"Cannot save per-call stages");});''')
s = replace(s, 'auto stage=[&](const char*name,int64_t value){journal<<', 'auto stage=[&](const char*name,int64_t value){trace.run(phase::Phase::JournalFlush,value,[&]{journal<<')
s = replace(s, 'need(bool(journal),"Stage save failed");};', 'need(bool(journal),"Stage save failed");});};')
s = replace(s, 'auto zg=p_->device.cast<xrt::ZG330Device>();const auto resetBegin=now();p_->device.reset(1);const auto before=zg.layerCount();need(before==0,"Independent counter not zero at frame boundary");', '''auto zg=p_->device.cast<xrt::ZG330Device>();
    trace.run(phase::Phase::Deadline,-1,[&]{need(phase::beforeDeadline(planned,now()),"Prepared call missed absolute slot; no forward");});trace.check();
    const auto resetBegin=now();const auto before=trace.run(phase::Phase::Reset,-1,[&]{p_->device.reset(1);const auto v=zg.layerCount();need(v==0,"Independent counter not zero at frame boundary");return v;});''')
s = replace(s, 'auto outputs=p_->session.forward(inputs);', 'auto outputs=trace.run(phase::Phase::Forward,-1,[&]{return p_->session.forward(inputs);});')
s = replace(s, 'checkStorage(t,p_->outs[i].tensorType(),p_->device.defaultMemRegion());', 'trace.run(phase::Phase::OutputStorage,outputIds[i],[&]{checkStorage(t,p_->outs[i].tensorType(),p_->device.defaultMemRegion());});')
s = replace(s, 'need(t.waitForReady(std::chrono::milliseconds(10000)),"Independent output readiness timeout");', 'trace.run(phase::Phase::Wait,outputIds[i],[&]{need(t.waitForReady(std::chrono::milliseconds(10000)),"Independent output readiness timeout");});')
s = replace(s, 'auto host=xrt::Tensor(t.dtype()).mallocOn(xrt::HostDevice::MemRegion());', 'auto host=trace.run(phase::Phase::OutputAllocate,outputIds[i],[&]{return xrt::Tensor(t.dtype()).mallocOn(xrt::HostDevice::MemRegion());});')
s = replace(s, 'host.copyFrom(0,t,0,outputSizes[i]);', 'trace.run(phase::Phase::Copy,outputIds[i],[&]{host.copyFrom(0,t,0,outputSizes[i]);});')
s = replace(s, 'host.read(bytes.data(),0,bytes.size());', 'trace.run(phase::Phase::HostRead,outputIds[i],[&]{host.read(bytes.data(),0,bytes.size());});')
s = replace(s, 'saveFile(out/("output-"+std::to_string(outputIds[i])+".f32"),bytes);', 'trace.run(phase::Phase::SaveOutput,outputIds[i],[&]{saveFile(out/("output-"+std::to_string(outputIds[i])+".f32"),bytes);});')
# Rename original textual trace stream to keep the observer reference unambiguous.
s = s.replace('std::ostringstream trace;trace<<', 'std::ostringstream report;report<<').replace('trace<<', 'report<<')
s = replace(s, 'saveText(out/"trace.json",trace.str());', 'trace.run(phase::Phase::SaveTrace,-1,[&]{saveText(out/"trace.json",report.str());});')

a = (src / 'producer_vpu_check.cpp').read_text().replace('"producer_sdk.hpp"', '"producer_phase_sdk.hpp"').replace('SdkGroup', 'SdkPhaseGroup')
a = replace(a, 'std::exception_ptr failure;', 'pose::producer_phase::Trace phases;\n    std::exception_ptr failure;')
a = replace(a, 'using Clock=std::chrono::steady_clock;', 'using Clock=std::chrono::steady_clock;using Phase=pose::producer_phase::Phase;')
a = replace(a, 'const auto planned=pose::producer_schedule::due(epoch,i);', 'phases.invocation(i);const auto planned=pose::producer_schedule::due(epoch,i);')
a = replace(a, 'std::this_thread::sleep_until(Clock::time_point(std::chrono::nanoseconds(planned)));', 'phases.run(Phase::Sleep,-1,[&]{std::this_thread::sleep_until(Clock::time_point(std::chrono::nanoseconds(planned)));});')
a = replace(a, 'if(video){video->check();observer->check();}\n            const auto dir', 'phases.run(Phase::VideoCheck,-1,[&]{if(video){video->check();observer->check();}});\n            const auto dir')
a = replace(a, 'fs::create_directory(dir);const auto&p=payload[i%2];', 'phases.run(Phase::Directory,-1,[&]{fs::create_directory(dir);});const auto&p=payload[i%2];')
a = replace(a, 'saveFile(dir/"input-486.f32",p.inputs[0]);saveFile(dir/"input-478.f16",p.inputs[1]);', 'phases.run(Phase::SaveInput,486,[&]{saveFile(dir/"input-486.f32",p.inputs[0]);});phases.run(Phase::SaveInput,478,[&]{saveFile(dir/"input-478.f16",p.inputs[1]);});')
a = replace(a, 'saveText(dir/"identity.json",', 'phases.run(Phase::SaveIdentity,-1,[&]{saveText(dir/"identity.json",')
a = replace(a, '\\"no_catch_up\\":true}\\n");', '\\"no_catch_up\\":true}\\n");});')
a = replace(a, 'sdk->forwardSave(p,dir,i);compareSaved(dir,p);saveText(dir/"comparison.json",', 'phases.run(Phase::SdkCall,-1,[&]{sdk->forwardSave(p,dir,i,phases,planned);});phases.run(Phase::Compare,-1,[&]{compareSaved(dir,p);});phases.run(Phase::SaveComparison,-1,[&]{saveText(dir/"comparison.json",')
a = replace(a, '\\"bitwise_equal\\":true}\\n");', '\\"bitwise_equal\\":true}\\n");});')
a = replace(a, '++completed;if(video){video->check();observer->check();}need(now()-actual<pose::producer_schedule::period,"Call exhausted slot; no catch-up");', '++completed;phases.run(Phase::EndCheck,-1,[&]{if(video){video->check();observer->check();}need(pose::producer_phase::beforeDeadline(planned,now()),"Call exhausted absolute slot; no catch-up");});phases.check();')
a = replace(a, 'video.reset();observer.reset();', 'video.reset();observer.reset();\n    if(!out.empty()&&fs::is_directory(out)){try{phases.save(out/"phases.jsonl");phases.check();}catch(...){if(!failure){failure=std::current_exception();}}}')

for path, text in ((include / 'producer_phase_sdk.hpp', h), (src / 'producer_phase_sdk.cpp', s), (src / 'producer_phase_check.cpp', a)):
    assert not path.exists(), path
    path.write_text(text, encoding='utf-8', newline='\n')
out = R / '.local/pose-v1-phase-preparation'
out.mkdir(exist_ok=True)
(out / 'sdk.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), s.splitlines(True), fromfile='frozen-producer_sdk.cpp', tofile='producer_phase_sdk.cpp')), encoding='utf-8')
print('Generated isolated diagnostics; frozen producer SDK and VPU unchanged')
