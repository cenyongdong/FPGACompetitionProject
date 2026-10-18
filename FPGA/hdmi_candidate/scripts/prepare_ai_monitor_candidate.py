"""Isolate the r5 project and add a passive, separately owned CSR observer."""
from pathlib import Path
import hashlib,json,re,shutil,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r1'
W=R/'.local/hdmi-live-20261017-r1'
old=R/'.local/hdmi-integration-20261016-r1/reference';new=W/'reference'
assert json.loads((E/'sim-ai-monitor-r1/result.json').read_text())['passed']
assert not new.exists()
started=time.monotonic();count=0;total=0
def copy(src,dst):
    global count,total
    if time.monotonic()-started>180:raise TimeoutError('Project copy budget; retain partial tree')
    shutil.copy2(src,dst);count+=1;total+=Path(src).stat().st_size
    if count%500==0:print(json.dumps({'copied_files':count,'seconds':time.monotonic()-started}),flush=True)
    return dst
def ignore(directory,names):
    banned={'.Xil','fpai_demo_vivado.sim','fpai_demo_vivado.hw'}
    if Path(directory).name=='fpai_demo_vivado.runs':
        banned|={n for n in names if n=='synth_1' or not n.endswith('_synth_1')}
    return [n for n in names if n in banned or n.endswith(('.jou','.backup.log'))]
shutil.copytree(old,new,copy_function=copy,ignore=ignore)
remapped=[]
for p in new.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.xpr','.tcl','.bat','.xml','.xci','.log','.rpt','.xdc'}:continue
    try:s=p.read_text(encoding='utf-8')
    except UnicodeError:continue
    changed=s.replace(old.as_posix(),new.as_posix()).replace(str(old),str(new))
    if changed!=s:p.write_text(changed,encoding='utf-8');remapped.append(p.relative_to(new).as_posix())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(new/'rtl').as_posix():sha(p) for p in (new/'rtl').rglob('*') if p.is_file()}
peripheral=new/'rtl/ps_ai_peripheral.sv';s=peripheral.read_bytes().decode('latin1')
assert s.count('.upstream(cam.slave)')==1
s=s.replace('.upstream(cam.slave)','.upstream(diag_passthrough.slave)')
anchor='  mna_gp_ww_itf hdmi_csr();';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n  mna_gp_ww_itf diag_passthrough();\n  mna_gp_ww_itf ai_diag_csr();')
addition=r'''
// Passive observer: a second reserved camera alias, independent of HDMI CSR.
hdmi_cam_router #(.HDMI_BASE(32'h400b0100)) ai_diag_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cam.slave),
 .camera(diag_passthrough.master),.hdmi(ai_diag_csr.master));
wire ai_mon_aw=pl_awvalid && pl_awready;
wire ai_mon_b=pl_bvalid && pl_bready;
wire ai_mon_cmd=app_en && app_rdy;
wire ai_mon_wdf=app_wdf_wren && app_wdf_rdy;
wire ai_mon_ar=pl_arvalid && pl_arready;
wire ai_mon_r=pl_rvalid && pl_rready;
wire [15:0] ai_mon_events={1'b1,!ddr3_init_done,
 app_wdf_wren && !app_wdf_rdy,pl_awvalid && !pl_awready,
 ai_mon_r && pl_rlast,ai_mon_r,ai_mon_ar,app_rd_data_valid,
 ai_mon_cmd && app_cmd==3'd1,ai_mon_wdf && app_wdf_end,
 ai_mon_wdf,ai_mon_cmd && app_cmd==3'd0,
 pl_bvalid,ai_mon_b,ai_mon_aw && pl_awlast,ai_mon_aw};
// Bits 14:13 reserved: do not sample raw asynchronous hard-reset inputs as data.
wire [31:0] ai_mon_flags={19'd0,1'b0,pl_rst_n,
 pl_rready,pl_rvalid,pl_bready,pl_bvalid,pl_awlast,pl_awready,
 pl_awvalid,app_wdf_rdy,app_rdy,ddr_ui_rst,ddr3_init_done};
wire [7:0] ai_mon_sample_update={ai_mon_wdf,ai_mon_aw,
 ai_mon_aw && pl_awlast,ai_mon_ar,ai_mon_cmd,ai_mon_aw,ai_mon_aw,1'b1};
wire [255:0] ai_mon_sample_data={app_wdf_data[31:0],pl_awdata[31:0],
 {5'd0,pl_awaddr},{5'd0,pl_araddr},{app_cmd,app_addr},
 {25'd0,pl_awinfo,pl_awlast},{5'd0,pl_awaddr},ai_mon_flags};
ai_event_monitor ai_path_monitor(
 .source_clk(hp_clk),.csr_clk(gp_clk),.resetn(sys_rst_n & FCLK_RESET0_N),
 .events(ai_mon_events),.sample_update(ai_mon_sample_update),
 .sample_data(ai_mon_sample_data),.csr(ai_diag_csr.slave));
'''
index=s.index('// Candidate exclusively owns HP2 AR/R.')
s=s[:index]+addition+s[index:];peripheral.write_bytes(s.encode('latin1'))
shutil.copyfile(R/'FPGA/hdmi_candidate/diagnostics/ai_event_monitor.sv',new/'rtl/hdmi_candidate/ai_event_monitor.sv')

# Extend the already-qualified two clock-pair scoping to the new observer only.
# Old AI/DDR exceptions and all nine HDMI core modules remain untouched.
for name in ['hdmi_cdc.tcl','hdmi_cdc.xdc']:
    p=new/'constrs_1'/name;s=p.read_text(encoding='utf-8')
    s=s.replace('{NAME !~ U0_ps_ai_peripheral/hdmi_display/*}',
                '{NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/*}')
    s=s.replace('set new_launch [filter $all_launch {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]',
                'set new_launch [filter $all_launch {NAME =~ U0_ps_ai_peripheral/hdmi_display/* || NAME =~ U0_ps_ai_peripheral/ai_path_monitor/*}]')
    p.write_text(s,encoding='utf-8')

after={p.relative_to(new/'rtl').as_posix():sha(p) for p in (new/'rtl').rglob('*') if p.is_file()}
changed=[n for n,h in before.items() if after[n]!=h]
assert changed==['ps_ai_peripheral.sv'],changed
added=sorted(after.keys()-before.keys());assert added==['hdmi_candidate/ai_event_monitor.sv']
result={'files_copied':count,'bytes':total,'seconds':time.monotonic()-started,'copy_budget':180,
        'metadata_remapped':remapped,'changed_existing_RTL':changed,'added_RTL':added,
        'RTL_before':before,'RTL_after':after,'new_CSR':'0x400b0100..0x400b01ff',
        'HDMI_CSR_and_data_path_unchanged':True,'AI_DDR_logic_unchanged':True,
        'source_clock':'hp_clk, same net as pl_itf_clk; clk_pll_i=200MHz',
        'BOOT_or_board_write':False}
(E/'monitor-candidate-preparation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
out=E/'monitor-candidate-source';out.mkdir()
shutil.copyfile(peripheral,out/'ps_ai_peripheral.sv')
shutil.copyfile(new/'rtl/hdmi_candidate/ai_event_monitor.sv',out/'ai_event_monitor.sv')
for name in ['hdmi_cdc.tcl','hdmi_cdc.xdc']:shutil.copyfile(new/'constrs_1'/name,out/name)
print(json.dumps({k:result[k] for k in ['files_copied','bytes','seconds','changed_existing_RTL','added_RTL']}),flush=True)
