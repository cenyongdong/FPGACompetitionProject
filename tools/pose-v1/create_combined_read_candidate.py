"""Generate an isolated composition; never modify the frozen successful sources."""
import json,shutil
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def fresh(p,s):
    p=root/p;assert not p.exists(),p;p.write_text(s,encoding='utf-8',newline='\n')
main=read('software/pose_v1/src/tensor_identity_check_r1.cpp')
main=main.replace('#include "bounded_load_contract.hpp"','#include "bounded_load_contract.hpp"\n#include "combined_read_contract.hpp"',1)
main=main.replace('namespace load=pose::bounded_load;','namespace load=pose::bounded_load;namespace policy=pose::combined_read;',1)
main=main.replace('load::networkSeconds','policy::networkSeconds').replace('load::readyDurationNs','policy::readyDurationNs')
main=main.replace('std::chrono::seconds(6)','std::chrono::seconds(5)',1)
main=main.replace('input.finish(out,mode=="process-three",','input.finish(out,true,',1)
main=main.replace('(mode=="load-103"||(stats.consumed==measured.size()&&stats.overwritten==0&&stats.coalesced==0))','(stats.consumed==measured.size()&&stats.overwritten==0&&stats.coalesced==0)',1)
fresh('software/pose_v1/src/combined_read_check.cpp',main)
cm=read('tools/pose-v1/input-read-CMakeLists.txt')
block=cm[cm.index('add_executable(pose_live_pipeline_check '):cm.index('add_executable(pose_access_unit_selftest ')]
new=block.replace('pose_live_pipeline_check','pose_combined_read_check').replace('forward_trace_check.cpp','combined_read_check.cpp').replace('application_bridge.cpp','read_input_bridge.cpp input_read_sdk.cpp input_read_contract.cpp')
fresh('tools/pose-v1/combined-read-CMakeLists.txt',cm+new)
ps=read('tools/pose-v1/Build-InputRead.ps1').replace('mixed-20261010-input-read-r1','mixed-20261010-combined-read-r1')
ps=ps.replace("'--parallel','2'","'pose_combined_read_check','--parallel','2'",1)
ps=ps.replace('$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_combined_read_check'),(Join-Path $poseOutput 'pose_combined_read_check'))\nInvoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_combined_read_check'))\n$poseHashes = [ordered]@{}",1)
ps=ps.replace("    stage='compiled_not_executed';","    combined_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_combined_read_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    stage='compiled_not_executed';",1)
fresh('tools/pose-v1/Build-CombinedRead.ps1',ps)
base=read('tools/pose-v1/review_input_read_build_base.py').replace('Build-InputRead.ps1','Build-CombinedRead.ps1').replace("'input_read_frozen_sources')","'input_read_frozen_sources','combined_read_frozen_sources')").replace('len(sections)==8','len(sections)==9')
fresh('tools/pose-v1/review_combined_read_build_base.py',base)
review=read('tools/pose-v1/review_tensor_identity_r3_stage.py')
start,end=review.index('def identities('),review.index('def main(')
review=review[:start]+'''from review_combined_read_build_base import identities as base_identities
def identities(package,build):
    m,b,n=base_identities(package,build)
    assert sha(build/'pose_combined_read_check')==b['combined_binary_sha256']
    return m,dict(b,binary_sha256=b['combined_binary_sha256']),n

'''+review[end:]
review=review.replace('run-tensor-identity.sh','run-combined-read.sh').replace("r/'pose_live_pipeline_check'","r/'pose_combined_read_check'")
review=review.replace("if a.stage in ('process-three',):","if a.stage in ('process-three','load-103'):")
review=review.replace("whole_5Hz_threshold_met=bool(a.stage=='load-103' and rate>=5 and metrics['arrival_to_picture_ms']['P95']<=500 and ingress['overwritten']==0)","whole_5Hz_threshold_met=False,input_fps=2,diagnostic_2Hz_not_performance_acceptance=True")
fresh('tools/pose-v1/review_combined_read_stage.py',review)
runner=read('tools/pose-v1/run-tensor-identity.sh').replace('pose_live_pipeline_check','pose_combined_read_check').replace("b['binary_sha256']","b['combined_binary_sha256']")
# Gate schema uses binary_sha256 for this independent executable.
runner=runner.replace('free -m > "$run/memory.before.txt"','free -m > "$run/memory.before.txt"\nfor n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done')
runner=runner.replace('free -m > "$run/memory.after.txt"','free -m > "$run/memory.after.txt"\nfor n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done\nps -eo pid,comm,args > "$run/final.processes"\nss -ltnp > "$run/final.ports"')
runner=runner.replace('    job=$!','    job=$!\n    test "$stage" != host-check || exit 1',1)
fresh('tools/pose-v1/run-combined-read.sh',runner)
client=read('tools/pose-v1/bounded_live_rtsp_client.py').replace('start<105','start<125')
fresh('tools/pose-v1/combined_read_rtsp_client.py',client)
peer=read('tools/pose-v1/bounded_load_peer_ready.py').replace('from bounded_live_rtsp_client','from combined_read_rtsp_client').replace("'bounded_live_rtsp_client.py'","'combined_read_rtsp_client.py'")
fresh('tools/pose-v1/combined_read_peer.py',peer)
base=root/'.local/pose-v1-input-read/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
m['combined_read_frozen_sources']={rel:v['sha256'] for rel,v in m['build_files'].items()}
m['build_files'].pop('tools/pose-v1/input-read-CMakeLists.txt')
for rel,dest in [('tools/pose-v1/combined-read-CMakeLists.txt','CMakeLists.txt'),('software/pose_v1/include/combined_read_contract.hpp','combined_read_contract.hpp'),('software/pose_v1/src/combined_read_check.cpp','combined_read_check.cpp')]:m['build_files'][rel]=dict(destination=dest,sha256=g.sha(root/rel))
for name in ['create_combined_read_candidate.py','Build-CombinedRead.ps1','run-combined-read.sh','review_combined_read_build_base.py','review_combined_read_stage.py','combined_read_rtsp_client.py','combined_read_peer.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-CombinedRead.ps1';m['combined_read']=dict(input_fps=2,sent=103,ready_seconds=60,network_seconds=120,client_seconds=125,hardware_seconds=180,encoding_limit=1000,device_input='public read',strict_coverage=True,HDMI=False)
out=root/'.local/pose-v1-combined-read/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
