"""Final identities and full local delivery manifest; never rewrites prior completion evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];E1=E.parent/'shared-stability-20261015-r1'
D=R/'.local/shared-stability-delivery-20261015-r2'
S=R/'.local/shared-resident-source-20261015-r1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
assert not (E/'completion-review.json').exists()
a=load(E/'stress-analysis.json');assert a['status']=='passed' and a['inferences']==62945
assert load(E/'final-cleanup-review.json')['passed']
assert not load(E/'publication-review.json')['new_missing']
package=load(E/'package.json');assert sha(D/'package.json')=='c4f3fbd4ee9abd7bc5ac8cc7807d0022d4f58906a569b28fbc0c3f4aacde71c3'
assert (E/'package.json').read_bytes()==(D/'package.json').read_bytes()
for name,digest in package['files'].items():assert sha(D/name)==digest,('package',name)
assert sha(D/'pose_shared_timing')==package['binary_sha256']
assert sha(D/'pose_shared_resident')==package['resident_binary_sha256']
for name in ('pose_shared_timing','pose_shared_resident'):
 assert sha(D/name)==sha(R/'.local/shared-stability-delivery-20261015-r1'/name),('r2 binary unchanged',name)
source=load(E1/'resident-source-manifest.json')
for name,digest in source['files'].items():assert sha(S/name)==digest,('frozen source',name)
review=load(E/'short-reviewed.json');assert sha(E/'short-analysis.json')==review['source_report_sha256']
assert review['approved_to_start_stress'] and review['package_sha256']==sha(D/'package.json')
for stage,n in (('basic',3),('short',1131),('stress',62945)):
 assert int((E/('returned-'+stage)/('run-'+stage)/'exit.txt').read_text())==0
 assert load(E/(stage+'-analysis.json'))['inferences']==n
old=load(E1/'returned-basic/run-basic/controller-summary.json');assert old['exit']==1 and old['killed_child'] and not old['automatic_retry']
for item in load(E/'documentation-revision.json')['files']:assert sha(Path(item['path']))==item['after_sha256']
assert 'exited' in (E1/'docker-final-state.txt').read_text().lower()
check=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check'],cwd=R,capture_output=True)
(E/'diff-check.txt').write_bytes(check.stdout+check.stderr);assert check.returncode==0
entries={}
for root in (E1,E):
 for p in sorted(root.rglob('*')):
  if not p.is_file() or any(v in p.parts for v in ('__pycache__','mpl-config')):continue
  if p.parent==E and p.name in ('completion-review.json','delivery-files.json'):continue
  entries[p.relative_to(R).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
save(E/'delivery-files.json',dict(files=entries,note='Excludes this manifest, completion-review, interpreter/plot caches. Includes full raw streams and original r1 failure.'))
result=dict(status='completed_numeric_memory_crash_observation_scope_with_latency_tail_open',completed_at_UTC=datetime.now(timezone.utc).isoformat(),
 basic_inferences=3,short_inferences=1131,stress_inferences=62945,stress_seconds=a['duration']['actual_duration_ms']/1000,
 unique_input_sources=3,all_actual_arrays_independently_checked=True,memory_growth_screen_passed=True,
 same_graph_repeat_pose_changes=a['same_graph_repeat_pose_changed_frames'],no_crash_or_SDK_error_observed=True,
 latency_tail=dict(open_difficulty='D41',count_over_1_second=11,max_process_ms=a['timing_ms']['process_ms']['max'],cause='unknown',hard_real_time_pass=False),
 SDK_BOOT_model_unchanged=True,original_compiled_binary_unchanged=True,r1_failure_preserved=True,r2_restart_explicitly_authorized=True,
 no_inference_retry_or_budget_extension=True,all_owned_processes_and_connections_ended=True,FPAI_restored_exited=True,
 hardware_temperature_unavailable=True,old_DATA_investigation_resumed=False,formal_demo_replaced=False,
 package_sha256=sha(D/'package.json'),resident_binary_sha256=package['resident_binary_sha256'],
 source_archive_sha256=sha(E1/'source.tar.gz'),raw_stress_bytes=62945*60400,
 delivery_file_count=len(entries),delivery_manifest_sha256=sha(E/'delivery-files.json'),
 report_sha256=sha(E/'REPORT.md'),documentation_revision_sha256=sha(E/'documentation-revision.json'),
 scope='Finite 30-minute serial loop over three frozen inputs, with full output saving and no video/network overlay; no universal no-leak or worst-case latency guarantee')
save(E/'completion-review.json',result)
print(json.dumps(result,indent=2,ensure_ascii=False))
