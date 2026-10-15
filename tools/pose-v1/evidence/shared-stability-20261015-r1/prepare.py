"""Fresh package: frozen compiled validation binary plus same-core resident test entry."""
from pathlib import Path
import ast,hashlib,json,shutil
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
OLD=R/'.local/shared-confidence-source-20261015-r1';OLD_D=R/'.local/shared-confidence-delivery-20261015-r1'
S=R/'.local/shared-resident-source-20261015-r1';D=R/'.local/shared-stability-delivery-20261015-r1'
T=R/'.local/shared-stability-transport-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not S.exists() and not D.exists() and not T.exists()
expected=json.loads((R/'tools/pose-v1/evidence/shared-confidence-gate-20261015-r1/completion-review.json').read_text(encoding='utf-8'))
assert sha(OLD_D/'pose_shared_timing')==expected['ARM_binary_sha256']
original=json.loads((OLD/'source-manifest.json').read_text(encoding='utf-8'))
for n,h in original['files'].items():assert sha(OLD/n)==h,n
shutil.copytree(OLD,S,ignore=shutil.ignore_patterns('source-manifest.json'))
shutil.copytree(OLD_D,D,ignore=shutil.ignore_patterns('package.json'))
shutil.copyfile(E/'resident_validation.cpp',S/'resident_validation.cpp')
prefix=(S/'main.cpp').read_text(encoding='utf-8').split('int main(int argc, char** argv)')[0]
(S/'resident_support.hpp').write_text('#pragma once\n'+prefix,encoding='utf-8',newline='\n')
p=S/'CMakeLists.txt';s=p.read_text(encoding='utf-8').replace('pose_shared_timing','pose_shared_resident').replace(' main.cpp',' resident_validation.cpp');p.write_text(s,encoding='utf-8',newline='\n')

def edit(rel,old,new):
    p=S/'baseline'/rel;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(rel,old)
    p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
edit('host_stage_observation.hpp','CopyObserver observer = {});','CopyObserver observer = {}, uint64_t metadata_invocation_limit = UINT64_MAX);')
edit('host_stage_observation.cpp','bool configured = false;','bool configured = false;\n        uint64_t metadata_invocation_limit = UINT64_MAX;')
edit('host_stage_observation.cpp','void configure(const std::filesystem::path& path, CopyObserver callback) {',
     'void configure(const std::filesystem::path& path, CopyObserver callback, uint64_t limit) {')
edit('host_stage_observation.cpp','observer = std::move(callback);','observer = std::move(callback);\n        metadata_invocation_limit = limit;')
edit('host_stage_observation.cpp','append(s.str());\n        // Observe owned shadow bytes;',
     'if (invocation_ < metadata_invocation_limit) append(s.str());\n        // Observe owned shadow bytes;')
edit('tensor_identity_observation.hpp','void configure(const std::filesystem::path &);',
     'void configure(const std::filesystem::path &, uint64_t invocation_limit = UINT64_MAX);')
edit('tensor_identity_observation.cpp','std::unique_ptr<Recorder > recorder;',
     'std::unique_ptr<Recorder > recorder;\n        uint64_t invocation_limit = UINT64_MAX;')
edit('tensor_identity_observation.cpp','void configure(const std::filesystem::path& out) {',
     'void configure(const std::filesystem::path& out, uint64_t limit) {')
edit('tensor_identity_observation.cpp','root = out;','root = out;\n        invocation_limit = limit;')
edit('tensor_identity_observation.cpp','if (recorder) recorder->sample(f, i, op, slot, after, std::move(p));',
     'if (recorder && i < invocation_limit) recorder->sample(f, i, op, slot, after, std::move(p));')
p=S/'resident_validation.cpp';s=p.read_text(encoding='utf-8').replace('configure(output/"copy-observations");','configure(output/"copy-observations", {}, 3);').replace('configure(output/"tensor-identities");','configure(output/"tensor-identities", 3);');p.write_text(s,encoding='utf-8',newline='\n')
changed=[]
for n,h in original['files'].items():
    if sha(S/n)!=h:changed.append(n)
allowed={'CMakeLists.txt','baseline\\host_stage_observation.hpp','baseline\\host_stage_observation.cpp',
         'baseline\\tensor_identity_observation.hpp','baseline\\tensor_identity_observation.cpp'}
assert set(changed)==allowed,changed
manifest=dict(status='resident_test_source_prepared_not_board_executed',origin=str(OLD),
    changed_original_files=changed,core_math_CPU_registration_NPU_allocation_model_unchanged=True,
    normal_observation_frames=3,failure_Host_shadow_and_two_source_reads_preserved=True,
    files={str(p.relative_to(S)):sha(p) for p in sorted(S.rglob('*')) if p.is_file()})
save(S/'source-manifest.json',manifest);save(E/'resident-source-manifest.json',manifest);save(D/'resident-source-manifest.json',manifest)
shutil.copyfile(E/'run_stage.py',D/'run_stage.py')
ast.parse((D/'run_stage.py').read_text(encoding='utf-8'))
plan=dict(basic=dict(seconds=0,max_frames=3,wall_timeout_seconds=160,memory_warmup_seconds=0),
    short=dict(seconds=30,max_frames=3000,wall_timeout_seconds=140,memory_warmup_seconds=10),
    stress=dict(seconds=1800,max_frames=90000,wall_timeout_seconds=1940,memory_warmup_seconds=30),
    authorization='User explicitly selected30minutes continuous full-speed inference, max90000, after short validation',
    data='Repeat three frozen CSI windows; distinguish inference count from unique samples',
    resources=dict(RSS_limit_MiB=512,RSS_growth_stop_MiB=64,minimum_MemAvailable_MiB=96,
                   minimum_disk_free_GiB=2,fd_growth_limit=16,thread_growth_limit=8),
    no_video_or_TCP=True,no_reboot_or_drop_caches=True,no_auto_retry=True,
    saved_actual_bytes_per_inference=60400,maximum_raw_bytes=5436000000)
save(E/'plan.json',plan);save(D/'plan.json',plan)
T.mkdir();text=(R/'.local/shared-gate-transport-20261015-r1/secure_transport.py').read_text(encoding='utf-8')
(T/'secure_transport.py').write_text(text.replace('/tmp/wifi-pose-shared-gate-20261015-r1/','/tmp/wifi-pose-shared-stability-20261015-r1/'),encoding='utf-8')
print(json.dumps(dict(source=str(S),delivery=str(D),original_binary_sha256=sha(D/'pose_shared_timing'),changed=changed)))
