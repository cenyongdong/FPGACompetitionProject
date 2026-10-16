"""Freeze r1 reports/run before correcting unused legacy PHY and scoped constraints."""
from pathlib import Path
import hashlib,json,zipfile,shutil
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1';W=R/'.local/hdmi-integration-20261016-r1';F=W/'reference'
assert json.loads((E/'constraint-binding/execution.json').read_text())['exit']==0
D=E/'topology-revision-r2';D.mkdir(exist_ok=False)
run=F/'fpai_demo_vivado.runs/synth_1';ids={}
with zipfile.ZipFile(D/'r1-synthesis-run.zip','w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for p in run.rglob('*'):
  if p.is_file():
   n=p.relative_to(run).as_posix();ids[n]=hashlib.sha256(p.read_bytes()).hexdigest();z.write(p,n)
with zipfile.ZipFile(D/'r1-synthesis-run.zip') as z:
 assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in ids.items())
(D/'r1-synthesis-run-manifest.json').write_text(json.dumps(ids,indent=2)+'\n')
shutil.copyfile(F/'rtl/hdmi_candidate/hdmi_clock_jfm.v',D/'hdmi_clock_jfm-r1.v')
shutil.copyfile(F/'constrs_1/hdmi_cdc.xdc',D/'hdmi_cdc-r1.xdc')
p=F/'rtl/display/frame_to_ps_largebuf.v';text=p.read_bytes().decode('latin1')
shutil.copyfile(p,D/p.name)
start=text.index('    cmos_clkgen_742_5 cmos_clkgen_742_5_u0')
end=text.index('    always @(posedge cam_clk_use)',start)
text=text[:start]+'    generate if(!CANDIDATE_SCANOUT) begin : legacy_clock\n'+text[start:end]+'    end endgenerate\n\n'+text[end:]
start=text.index('    uihdmitx #(.FAMILY("7FAMILY"))uihdmitx_inst(')
end=text.index('    always @(posedge m00_axi_aclk)',start)
text=text[:start]+'    generate if(!CANDIDATE_SCANOUT) begin : legacy_transmitter\n'+text[start:end]+'    end endgenerate\n\n'+text[end:]
p.write_bytes(text.encode('latin1'))
shutil.copyfile(R/'FPGA/hdmi_candidate/rtl/integration/hdmi_clock_jfm.v',F/'rtl/hdmi_candidate/hdmi_clock_jfm.v')
shutil.copyfile(R/'FPGA/hdmi_candidate/constraints/hdmi_cdc.xdc',F/'constrs_1/hdmi_cdc.xdc')
shutil.copytree(F/'rtl/hdmi_candidate',D/'r2-integrated-rtl')
shutil.copyfile(p,D/'frame_to_ps_largebuf-r2.v')
shutil.copyfile(F/'constrs_1/hdmi_cdc.xdc',D/'hdmi_cdc-r2.xdc')
(D/'decision.json').write_text(json.dumps({'r1_synthesis_and_constraints_preserved':True,
 'new_findings':['Unused legacy PHY still existed in pre-opt synth netlist: six MMCMs for five sites','New BUFIO/BUFG mixed topology warned of phase alignment','Q-pin max-delay startpoints caused Constraints18-515 path segmentation'],
 'corrections':['Generate out legacy clock and TMDS instances for candidate parameter only','Same MMCM serial output drives BUFIO and divide-by-five BUFR','Use launch C pins rather than Q forced startpoints'],
 'inherited_preopt_NDRV_unchanged_nets':['S1_AXI_HP_HC_WID','pl_int_ready / PS7 outputs'],
 'post_factory_opt_DRC_still_required':True,'no_extra_DRC_or_timing_waiver':True},indent=2)+'\n')
print(json.dumps({'archived_r1_run_files':len(ids),'legacy_PHY_generated_out_for_candidate':True}))
