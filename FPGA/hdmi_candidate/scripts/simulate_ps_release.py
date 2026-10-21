"""Native directed tests for the passive recorder and old CSR regression."""
from pathlib import Path
import subprocess
import json
import sys
import argparse
import shutil
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'
parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=2);args=parser.parse_args()
E=E/('sim-r'+str(args.attempt));E.mkdir(exist_ok=False)
W=R/'.local/hdmi-ps-release-20261020-r26/sim'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')
W.mkdir(parents=True,exist_ok=True)
sources=[R/'.local/hdmi-boot-witness-20261019-r23/reference/rtl/utils/mna_itf.sv',
 R/'FPGA/hdmi_candidate/diagnostics/ps_release_witness.sv',
 R/'.local/hdmi-boot-witness-20261019-r23/reference/rtl/hdmi_candidate/hdmi_cam_router.sv',
 R/'FPGA/hdmi_candidate/diagnostics/ai_boot_witness.sv',
 R/'.local/hdmi-ps-release-20261020-r26/sources/ai_read_monitor.sv',
 R/'FPGA/hdmi_candidate/sim/tb_ps_release_witness.sv',
 R/'FPGA/hdmi_candidate/sim/tb_ai_read_monitor.sv']
(W/'run.tcl').write_text('run all\nquit\n')
commands=[('compile',[str(V/'xvlog.bat'),'--sv',*[str(x) for x in sources]]),
 ('elaborate',[str(V/'xelab.bat'),'tb_ps_release_witness','--timescale','1ns/1ps','--snapshot','release_unit']),
 ('simulate',[str(V/'xsim.bat'),'release_unit','--tclbatch','run.tcl']),
 ('legacy-elaborate',[str(V/'xelab.bat'),'tb_ai_read_monitor','--timescale','1ns/1ps','--snapshot','legacy_unit']),
 ('legacy-simulate',[str(V/'xsim.bat'),'legacy_unit','--tclbatch','run.tcl'])]
result=[]
for name,command in commands:
 with (E/('sim-'+name+'.log')).open('wb') as log:
  p=subprocess.run(command,cwd=W,stdout=log,stderr=subprocess.STDOUT)
 result.append({'stage':name,'exit_code':p.returncode,'command':command})
 (E/'sim-execution.json').write_text(json.dumps(result,indent=2))
 if p.returncode:raise SystemExit(name+' failed; see native log')
if 'PS_RELEASE_WITNESS_PASS' not in (E/'sim-simulate.log').read_text():raise SystemExit('No completed simulation')
if 'AI_READ_MONITOR_PASS' not in (E/'sim-legacy-simulate.log').read_text():raise SystemExit('Legacy CSR regression did not complete')
if (W/'native-release-snapshot.jsonl').is_file():
 shutil.copyfile(W/'native-release-snapshot.jsonl',E/'native-release-snapshot.jsonl')
 sys.path.insert(0,str(R/'FPGA/hdmi_candidate/software'))
 from decode_ps_release import decode
 decoded=decode(json.loads((E/'native-release-snapshot.jsonl').read_text())['words'])
 if decoded['raw_HP_handshakes']['legacy_AW']!=1 or decoded['first_PL_ready_PS_RVALID_HP_cycle']<2**32:
  raise SystemExit('Native CSR/decoder contract failed')
 (E/'decoded-native-snapshot.json').write_text(json.dumps(decoded,indent=2))
print('PS_RELEASE_WITNESS_PASS')
