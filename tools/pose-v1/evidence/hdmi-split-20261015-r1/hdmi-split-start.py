from pathlib import Path
import hashlib,json,shutil
R=Path('D:/FPGACompetitionProject');C=R/'FPGA/hdmi_candidate'
E=R/'tools/pose-v1/evidence/hdmi-split-20261015-r1'
E.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'tools/pose-v1/evidence/hdmi-resume-20261015-r1/candidate-source'
verified=[]
for p in old.rglob('*'):
 if p.is_file():
  rel=p.relative_to(old);actual=C/rel
  verified.append({'source':rel.as_posix(),'previous_sha':sha(p),'current_sha':sha(actual)})
assert all(v['previous_sha']==v['current_sha'] for v in verified),'Identity changed; stop'
for rev in ('r6','r7'):
 for base in (R/'.local',R/'tools/pose-v1/evidence'):
  assert not (base/('hdmi-candidate-sim-20261015-'+rev)).exists()
for name in ('xvlog.bat','xelab.bat','xsim.bat'):
 assert (Path('D:/Xilinx/Vivado/2019.1/bin')/name).is_file()
for n in ('PROJECT-PROGRESS.md','DIFFICULTIES.md','Done.md','REFERENCES.md','ARCHITECTURE-DISCUSSION-20261015.md'):
 p=E/'before'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/n,p)
shutil.copytree(C,E/'before/FPGA/hdmi_candidate')
(E/'preflight.json').write_text(json.dumps({'source_identity':verified,'source_count':len(verified),
 'user_authorized_new_r6_core_r7_pixel':True,'stage_budget_seconds':90,
 'user_acknowledged_r5_kernel_PASS_and_external_deadline':True,'r5_historical_exit1_preserved':True,
 'uihdmitx_fix_authorized':True,'board_download':False,'BOOT_change':False,'DATA_investigation':False},indent=2)+'\n')
print('Preflight verified',len(verified),'candidate files; fresh r6/r7; before snapshots saved')
