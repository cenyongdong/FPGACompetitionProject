"""Prepare an unapplied API separation patch; no SDK/board calls."""
from pathlib import Path
import difflib,json,hashlib
root=Path(__file__).resolve().parents[2]
changes={}
header='software/pose_v1/include/application_core.hpp';s=(root/header).read_text(encoding='utf-8')
assert 'diagnostic_frames=4' in s
changes[header]=s.replace('diagnostic_frames=4','diagnostic_frames=4; size_t timing_frames=0')
core='software/pose_v1/src/application_core.cpp';s=(root/core).read_text(encoding='utf-8');assert 'fc::sample_limit=c.diagnostic_frames;' in s
changes[core]=s.replace('fc::sample_limit=c.diagnostic_frames;','need(c.timing_frames<=32,"Timing sampling is bounded to32 frames");\n        fc::sample_limit=c.timing_frames?c.timing_frames:c.diagnostic_frames;')
entry='software/pose_v1/src/forward_trace_check.cpp';s=(root/entry).read_text(encoding='utf-8');assert 'cfg.diagnostic_frames=mode=="trace-5hz"?32:0;' in s
changes[entry]=s.replace('cfg.diagnostic_frames=mode=="trace-5hz"?32:0;','cfg.diagnostic_frames=0;cfg.timing_frames=mode=="trace-5hz"?32:0;')
patch=''.join(''.join(difflib.unified_diff((root/rel).read_text(encoding='utf-8').splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)) for rel,new in changes.items())
output=root/'tools/pose-v1/forward-trace-only.candidate.patch';assert not output.exists();output.write_text(patch,encoding='utf-8',newline='\n')
(output.with_suffix('.provenance.json')).write_text(json.dumps(dict(applied=False,compiled=False,hardware_executed=False,source_sha256={rel:hashlib.sha256((root/rel).read_bytes()).hexdigest() for rel in changes},note='Must use new isolated header/core/entry destinations; never apply to frozen baselines. Failure-only staged-input capture requires separate implementation.'),indent=2)+'\n')
