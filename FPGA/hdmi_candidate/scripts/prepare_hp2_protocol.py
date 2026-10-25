"""Overlay one passive native protocol checker on the qualified r30 design."""
from pathlib import Path
import argparse,json,re,xml.etree.ElementTree as ET
from prepare_hp2_cycletrace import once
from prepare_s01_isolation import block

R=Path(__file__).resolve().parents[3]

def main():
 p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True);a=p.parse_args()
 assets=a.asset_root.resolve();old=assets/'.local/hdmi-hp2-cycletrace-20261022-r30'
 oe=assets/'tools/pose-v1/evidence/hdmi-hp2-cycletrace-20261022-r30'
 w=assets/'.local/hdmi-protocol-checker-20261023-r31';e=assets/'tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r31'
 ip=w/'ip/hp2_native_protocol_checker'
 config={}
 for item in ET.parse(ip/'hp2_native_protocol_checker.xci').iter():
  if item.tag.rsplit('}',1)[-1]!='configurableElementValue':continue
  key=next((v for k,v in item.attrib.items() if k.rsplit('}',1)[-1]=='referenceId'),'')
  if key.startswith('PARAM_VALUE.'):config[key.split('.',1)[1]]=item.text
 capacities={key:int(config[key]) for key in ('MAX_RD_BURSTS','MAX_WR_BURSTS')}
 s=w/'sources';s.mkdir();(e/'qualified-r8').mkdir()
 t=(old/'sources/ps_ai.v').read_text()
 t=once(t,'    diagnostic_hp2_rdata);','    diagnostic_hp2_rdata,\n    diagnostic_hp2_write);')
 t=once(t,'  output [63:0] diagnostic_hp2_rdata;','  output [63:0] diagnostic_hp2_rdata;\n  output [152:0] diagnostic_hp2_write;')
 fields={'AWADDR':(0,32),'AWID':(32,6),'AWLEN':(38,4),'AWSIZE':(42,3),'AWBURST':(45,2),
  'AWLOCK':(47,2),'AWCACHE':(49,4),'AWPROT':(53,3),'AWQOS':(56,4),'AWVALID':(60,1),'AWREADY':(61,1),
  'WDATA':(62,64),'WID':(126,6),'WSTRB':(132,8),'WLAST':(140,1),'WVALID':(141,1),'WREADY':(142,1),
  'BID':(143,6),'BRESP':(149,2),'BVALID':(151,1),'BREADY':(152,1)}
 addition=''.join('  assign diagnostic_hp2_write[%s] = axi_interconnect_4_M00_AXI_%s;\n'%
  (str(bit) if width==1 else '%d:%d'%(bit+width-1,bit),name) for name,(bit,width) in fields.items())
 t=once(t,'  assign diagnostic_hp2_rdata =',addition+'  assign diagnostic_hp2_rdata =')
 (s/'ps_ai.v').write_text(t)
 t=(old/'sources/ps_ai_wrapper.sv').read_text()
 t=once(t,'    output [63:0] diagnostic_hp2_rdata,','    output [63:0] diagnostic_hp2_rdata,\n    output [152:0] diagnostic_hp2_write,')
 t=once(t,'  .diagnostic_hp2_rdata(diagnostic_hp2_rdata),','  .diagnostic_hp2_rdata(diagnostic_hp2_rdata),\n  .diagnostic_hp2_write(diagnostic_hp2_write),')
 (s/'ps_ai_wrapper.sv').write_text(t)
 original=(old/'sources/ps_ai_peripheral.sv').read_text();t=original
 t=once(t,'wire [63:0] diagnostic_hp2_rdata;','wire [63:0] diagnostic_hp2_rdata;\nwire [152:0] diagnostic_hp2_write;')
 t=once(t,'    .diagnostic_hp2_rdata(diagnostic_hp2_rdata),','    .diagnostic_hp2_rdata(diagnostic_hp2_rdata),\n    .diagnostic_hp2_write(diagnostic_hp2_write),')
 t=once(t,'.upstream(cycletrace_passthrough.slave),\n .camera(read_diag_passthrough.master)',
  '.upstream(protocol_passthrough.slave),\n .camera(read_diag_passthrough.master)')
 start=t.index(' .flags(',t.index('hp2_cycle_trace hp2_cycle_recorder('));end=t.index('),\n .csr',start)
 old_flags=t[start+8:end]
 # Existing flags bits 24:0 remain exactly as r30; new observer flags use only
 # its seven previously reserved upper bits. Existing startup windows remain.
 base_flags=old_flags.removeprefix("{7'd0,").removesuffix('}')
 if base_flags==old_flags:raise RuntimeError('Unexpected trace flag declaration')
 t=t[:start]+' .flags(hp2_diagnostic_flags'+t[end:]
 addition='''wire [159:0] diagnostic_pc_status;
wire diagnostic_pc_asserted,diagnostic_pc_system_resetn,diagnostic_pc_ready,diagnostic_pc_seen_reset;
wire [31:0] hp2_diagnostic_flags={3'd0,diagnostic_pc_asserted,diagnostic_pc_seen_reset,
 diagnostic_pc_ready,diagnostic_pc_system_resetn,BASE_FLAGS};
hp2_protocol_observer hp2_protocol_observer(
 .clk(diagnostic_hp2_clk),.ps_resetn(diagnostic_ps_resetn),.ps_read(diagnostic_hp2_read),
 .ps_rdata(diagnostic_hp2_rdata),.ps_write(diagnostic_hp2_write),
 .pc_status(diagnostic_pc_status),.pc_asserted(diagnostic_pc_asserted),
 .system_resetn(diagnostic_pc_system_resetn),.checker_ready(diagnostic_pc_ready),.seen_reset_low(diagnostic_pc_seen_reset));
mna_gp_ww_itf protocol_passthrough(),protocol_csr();
hdmi_cam_router #(.HDMI_BASE(32'h400b4000),.DECODE_LSB(14)) protocol_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cycletrace_passthrough.slave),
 .camera(protocol_passthrough.master),.hdmi(protocol_csr.master));
hp2_protocol_trace hp2_protocol_recorder(
 .source_clk(diagnostic_hp2_clk),.csr_clk(gp_clk),.csr_resetn(~gp_clk_rst),
 .ps_read(diagnostic_hp2_read),.ps_rdata(diagnostic_hp2_rdata),.ps_write(diagnostic_hp2_write),
 .pc_status(diagnostic_pc_status),.flags(hp2_diagnostic_flags),.csr(protocol_csr.slave));
'''.replace('BASE_FLAGS',base_flags)
 t=once(t,'// Six-boundary passive',addition+'\n// Six-boundary passive')
 if block(t,'AI_Mate ZGolo(','\nendmodule')[2]!=block(original,'AI_Mate ZGolo(','\nendmodule')[2]:raise RuntimeError('Functional AI wiring changed')
 new_ps=block(t,'ps_ai_wrapper ps_ai_wrapper_u0 (','AI_Mate ZGolo(')[2].replace('    .diagnostic_hp2_write(diagnostic_hp2_write),\n','')
 if new_ps!=block(original,'ps_ai_wrapper ps_ai_wrapper_u0 (','AI_Mate ZGolo(')[2]:raise RuntimeError('Functional PS wiring changed')
 (s/'ps_ai_peripheral.sv').write_text(t)
 def remap(t):return t.replace(old.as_posix(),w.as_posix()).replace(oe.as_posix(),e.as_posix())
 def protect(t):
  for op,join in [('!~','&&'),('=~','||')]:
   term='NAME '+op+' U0_ps_ai_peripheral/hp2_cycle_recorder/*'
   t=t.replace(term,term+' '+join+' NAME '+op+' U0_ps_ai_peripheral/hp2_protocol_recorder/* '+join+' NAME '+op+' U0_ps_ai_peripheral/hp2_protocol_observer/*')
  term='[string match U0_ps_ai_peripheral/hp2_cycle_recorder/* [get_property NAME $p]]'
  return t.replace(term,term+' || [string match U0_ps_ai_peripheral/hp2_protocol_recorder/* [get_property NAME $p]] || [string match U0_ps_ai_peripheral/hp2_protocol_observer/* [get_property NAME $p]]')
 for path in (old/'sources-r2').glob('*.tcl'):
  t=protect(remap(path.read_text())).replace((w/'sources-r2').as_posix(),s.as_posix())
  if path.name=='pre-opt.tcl':t+='\nsource {'+(R/'FPGA/hdmi_candidate/constraints/hp2_protocol_cdc.tcl').as_posix()+'}\n'
  (s/path.name).write_text(t)
 new_sources=[ip/'hdl/sc_util_v1_0_vl_rfs.sv',ip/'hdl/axi_protocol_checker_v2_0_vl_rfs.sv',ip/'synth/hp2_native_protocol_checker.sv']
 new_sources += [R/'FPGA/hdmi_candidate/diagnostics'/name for name in ('hp2_protocol_observer.sv','hp2_protocol_trace.sv')]
 t=remap((oe/'synthesis.tcl').read_text())
 t=once(t,'read_verilog -library xil_defaultlib -sv {',
  'read_ip {'+(ip/'hp2_native_protocol_checker.xci').as_posix()+'}\n'+
  'set_property generate_synth_checkpoint false [get_files {'+(ip/'hp2_native_protocol_checker.xci').as_posix()+'}]\n'+
  'read_verilog -library xil_defaultlib -sv {\n  '+'\n  '.join(p.as_posix() for p in new_sources[3:]))
 (e/'synthesis.tcl').write_text(t)
 t=remap((oe/'opt.tcl').read_text()).replace('opt-r8.dcp','opt.dcp')
 t=t.replace((R/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl').as_posix(),(s/'ps_release_factory_clocks.tcl').as_posix())
 (e/'opt.tcl').write_text(t)
 t=remap((oe/'route.tcl').read_text()).replace('opt-r2.dcp','opt.dcp')
 t=re.sub(r'read_checkpoint -incremental \{[^}]+\}','read_checkpoint -incremental {'+(old/'qualified-routed.dcp').as_posix()+'}',t)
 (e/'route.tcl').write_text(t)
 t=remap((oe/'final.tcl').read_text())
 anchor='report_timing -through $ready -max_paths 4 -file'
 t=once(t,anchor,'set protocol_validation_file {'+(e/'qualified-r8/hp2-protocol-native-facts.tsv').as_posix()+'}\nsource {'+(R/'FPGA/hdmi_candidate/constraints/hp2_protocol_validate.tcl').as_posix()+'}\n'+anchor)
 (e/'final.tcl').write_text(t)
 (e/'bit.tcl').write_text(remap((oe/'bit.tcl').read_text()).replace('impl_hp2_cycletrace_r30','impl_hp2_protocol_r31'))
 overlay=json.loads((oe/'source-overlay.json').read_text())
 overlay['replacements']={k:remap(v.replace('\\','/')) for k,v in overlay['replacements'].items()}
 overlay['additional_sources'] += [str(p) for p in new_sources]
 overlay['additional_constraint_sources']=[str(s/path.name) for path in (old/'sources-r2').glob('*.tcl')]
 overlay['additional_constraint_sources'] += [str(R/'FPGA/hdmi_candidate/constraints'/name) for name in ('hp2_protocol_cdc.tcl','hp2_protocol_validate.tcl')]
 overlay['protocol_checker']=dict(VLNV='xilinx.com:ip:axi_protocol_checker:2.0',revision=4,AXI='AXI3',DATA_WIDTH=64,ADDR_WIDTH=32,ID_WIDTH=6,**capacities,HAS_SYSTEM_RESET=1,LIGHT_WEIGHT=0,PC_MASTER_SIDE=0,input_register_cycles=1,xci=str(ip/'hp2_native_protocol_checker.xci'))
 overlay['scope']='One observational native full AXI3 checker, first-error raw capture, original two startup windows, unchanged AI four HC and S01 source isolation'
 (e/'source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
 (e/'state.json').write_text(json.dumps(dict(status='offline_protocol_checker_prepared',package_id='hp2-protocol-r31',
  authorization='2026-10-23 user approved the protocol-checker plan and autonomous continuation; board write/start scope checked separately before use.',
  caps=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0),actual_candidate_starts=0,actual_original_fallbacks=0,
  AI_four_HC_unchanged=True,S01_source_isolation_preserved=True,background_tasks=[],
  next='Complete actual native IP directed tests, synthesis and physical qualification.'),indent=2)+'\n')
 print(json.dumps(dict(prepared=True,work=str(w),evidence=str(e),AI_four_HC_unchanged=True)))

if __name__=='__main__':main()
