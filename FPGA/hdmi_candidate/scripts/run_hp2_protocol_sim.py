"""Exercise the actual generated native IP and immutable raw CSR capture."""
from pathlib import Path
import argparse,json,subprocess

R=Path(__file__).resolve().parents[3]
V=Path('D:/vivado18.3/Vivado/2018.3/bin')

def main():
 p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True)
 p.add_argument('--run-name',default='sim');p.add_argument('--ids-only',action='store_true')
 p.add_argument('--ip-directory',type=Path);p.add_argument('--observer-source',type=Path)
 p.add_argument('--work-root',type=Path);p.add_argument('--evidence-root',type=Path)
 a=p.parse_args();assets=a.asset_root.resolve()
 w=a.work_root.resolve() if a.work_root else assets/'.local/hdmi-protocol-checker-20261023-r31'
 e=a.evidence_root.resolve() if a.evidence_root else assets/'tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r31'
 run=w/a.run_name;run.mkdir()
 ip=a.ip_directory.resolve() if a.ip_directory else w/'ip/hp2_native_protocol_checker'
 sources=[ip/'hdl/sc_util_v1_0_vl_rfs.sv',ip/'hdl/axi_protocol_checker_v2_0_vl_rfs.sv',
  ip/'sim/hp2_native_protocol_checker.sv',
  assets/'.local/hdmi-boot-witness-20261019-r23/reference/rtl/utils/mna_itf.sv',
  assets/'.local/hdmi-boot-witness-20261019-r23/reference/rtl/hdmi_candidate/hdmi_cam_router.sv']
 diagnostics=R/'FPGA/hdmi_candidate/diagnostics'
 sources += [diagnostics/'hp2_cycle_trace.sv',
  a.observer_source.resolve() if a.observer_source else diagnostics/'hp2_protocol_observer.sv',
  diagnostics/'hp2_protocol_trace.sv']
 sources += [R/'FPGA/hdmi_candidate/sim'/name for name in ('tb_hp2_protocol.sv','tb_hp2_cycle_trace.sv','tb_hp2_protocol_trigger.sv')]
 (run/'run.tcl').write_text('run all\nquit\n')
 commands=[[str(V/'xvlog.bat'),'--sv','--work','xil_defaultlib','-i',str(ip/'hdl/verilog')]+[str(s) for s in sources]]
 for top in (('tb_hp2_protocol_ids',) if a.ids_only else ('tb_hp2_protocol','tb_hp2_cycle_trace','tb_hp2_protocol_trigger')):
  commands += [[str(V/'xelab.bat'),'xil_defaultlib.'+top,'-s',top,'-timescale','1ns/1ps'],
   [str(V/'xsim.bat'),top,'-tclbatch','run.tcl']]
 results=[]
 with (e/(a.run_name+'.stdout.log')).open('xb') as log:
  for command in commands:
   print(json.dumps({'running':command[0],'step':len(results)}),flush=True)
   proc=subprocess.run(command,cwd=run,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   log.write(proc.stdout);log.flush();results.append(dict(command=command,exit_code=proc.returncode))
   (e/(a.run_name+'-execution.json')).write_text(json.dumps(results,indent=2)+'\n')
   if proc.returncode:
    print(proc.stdout.decode(errors='replace')[-5000:]);raise SystemExit(proc.returncode)
 text=(e/(a.run_name+'.stdout.log')).read_text(errors='replace')
 if (a.ids_only and 'HP2_PROTOCOL_IDS_PASS' not in text) or (not a.ids_only and ('HP2_PROTOCOL_PASS' not in text or 'HP2_CYCLE_TRACE_PASS' not in text or 'HP2_PROTOCOL_TRIGGER_PASS' not in text)):
  raise RuntimeError('Native simulator exited without completing the directed checks; inspect raw log')
 capture=run/'native-protocol-case3.json'
 if capture.is_file():
  import sys
  sys.path.insert(0,str(R/'FPGA/hdmi_candidate/software'))
  from decode_hp2_protocol import decode
  raw=json.loads(capture.read_text());decoded=decode(raw)
  if not any(c['bit']==58 for c in decoded['first_checks']):raise RuntimeError('Native status decode differs')
  if not any(r['PS_ARID']==7 and r['PS_ARLEN']==3 and r['PS_ARVALID'] for r in decoded['rows']):
   raise RuntimeError('Actual native raw address decode differs')
  (e/(a.run_name+'-native-raw.json')).write_text(json.dumps(raw,indent=2)+'\n')
  (e/(a.run_name+'-native-decoded.json')).write_text(json.dumps(decoded,indent=2)+'\n')
 print(json.dumps({'passed':True,'native_IP_cases':2 if a.ids_only else 8,'trigger_cases':0 if a.ids_only else 4,'legacy_cycle_trace_regression':not a.ids_only}))

if __name__=='__main__':main()
