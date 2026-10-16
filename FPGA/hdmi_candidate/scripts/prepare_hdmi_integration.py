"""Create an isolated full-system integration from the qualified factory project."""
from pathlib import Path
import hashlib,json,shutil,time,re
R=Path(__file__).resolve().parents[3];NAME='hdmi-integration-20261016-r1'
E=R/'tools/pose-v1/evidence'/NAME;W=R/'.local'/NAME
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
docs=['Agents.md','PROJECT-PROGRESS.md','REFERENCES.md','DIFFICULTIES.md','Done.md','ARCHITECTURE-DISCUSSION-20261015.md',
 'FPGA/hdmi_candidate/INTEGRATION.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/BOARD-PLAN.md']
before={}
for name in docs:
 p=R/name;d=E/'before'/name;d.parent.mkdir(parents=True,exist_ok=True)
 s=p.read_text(encoding='utf-8-sig')
 if name=='Agents.md':s=re.sub(r'密码：[^，。\r\n]+','密码：[REDACTED]',s)
 d.write_text(s,encoding='utf-8');before[name]={'original_sha256':sha(p),'snapshot_sha256':sha(d)}
(E/'documentation-before.json').write_text(json.dumps(before,indent=2)+'\n')
old=R/'.local/hdmi-jfm-build-20261016-r1/reference';new=W/'reference'
started=time.monotonic();copied=0;size=0
def copy(src,dst):
 global copied,size
 if time.monotonic()-started>180:raise TimeoutError('Project copy budget reached, preserve partial tree')
 shutil.copy2(src,dst);copied+=1;size+=Path(src).stat().st_size;return dst
def ignore(path,names):
 banned={'.Xil','fpai_demo_vivado.sim','fpai_demo_vivado.hw'}
 if Path(path).name=='fpai_demo_vivado.runs':banned|={'impl_1','impl_r2','synth_1'}
 return [n for n in names if n in banned or n.endswith(('.jou','.backup.log'))]
shutil.copytree(old,new,copy_function=copy,ignore=ignore)
# Remap only project/run text metadata. Never patch protected vendor sources/IP logic.
remapped=[]
for p in new.rglob('*'):
 if not p.is_file() or p.suffix.lower() not in {'.xpr','.tcl','.bat','.xml','.xci','.log','.rpt'}:continue
 try:s=p.read_text(encoding='utf-8')
 except UnicodeError:continue
 updated=s.replace(old.as_posix(),new.as_posix()).replace(str(old),str(new))
 if updated!=s:p.write_text(updated,encoding='utf-8');remapped.append(p.relative_to(new).as_posix())
baseline={p.relative_to(new/'rtl').as_posix():sha(p) for p in (new/'rtl').rglob('*') if p.is_file()}
(E/'reference-rtl-before.json').write_text(json.dumps(baseline,indent=2)+'\n')
candidate={p.name:sha(p) for p in (R/'FPGA/hdmi_candidate/rtl').glob('*.v')}
(E/'candidate-rtl-before.json').write_text(json.dumps(candidate,indent=2)+'\n')
(E/'copy.json').write_text(json.dumps({'seconds':time.monotonic()-started,'files':copied,'bytes':size,'budget':180,'metadata_remapped':remapped},indent=2)+'\n')
support=(R/'FPGA/hdmi_candidate/scripts/jfm_build_support.py').read_text(encoding='utf-8')
support=support.replace("E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';W=R/'.local/hdmi-jfm-build-20261016-r1'", "E=R/'tools/pose-v1/evidence/"+NAME+"';W=R/'.local/"+NAME+"'")
(W/'integration_support.py').write_text(support,encoding='utf-8')
(E/'authorization.json').write_text(json.dumps({'user':'Approved integrating corrected HDMI into full system and board validation',
 'new_CSR_base':'0x400b0000','CSR_span':256,'camera_public_low_addresses_preserved':True,
 'HP2_read_owner':'new HDMI scanout','HP2_write_owner':'original camera path',
 'reference_clock':'100MHz AC14','pixel_target_MHz':148.5,'serial_target_MHz':742.5,
 'reboot_or_BOOT_write':False,'old_DATA_resume':False,'previous_two_min_period_waiver_preserved':True,
 'new_timing_violations_waived':False,'simulation_budget_per_stage':90,'EDA_initial_budget':180,
 'EDA_stage_ceiling':1800,'max_threads':2,'parallel_runs':1},indent=2)+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps({'copied_files':copied,'copied_bytes':size,'seconds':time.monotonic()-started,'metadata_remapped':len(remapped)}),flush=True)
