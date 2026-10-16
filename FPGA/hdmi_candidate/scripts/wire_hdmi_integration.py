"""Wire the validated reader into a fresh factory system, preserving camera writes."""
from pathlib import Path
import hashlib,json,shutil,re,sys
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1';W=R/'.local/hdmi-integration-20261016-r1';F=W/'reference'
assert (E/'copy.json').exists() and not (E/'integration-wiring.json').exists()
if sys.argv[1:]==['corrected-read-enable-r2']:
 failed=E/'wiring-attempt-r1';failed.mkdir(exist_ok=False)
 for rel in ['rtl/ai7030_edif_top.v','rtl/ps_ai_peripheral.sv']:
  dst=failed/Path(rel).name;shutil.copyfile(F/rel,dst)
  original=R/'.local/hdmi-jfm-build-20261016-r1/reference'/rel
  shutil.copyfile(original,F/rel)
 (failed/'failure.json').write_text(json.dumps({'reason':'read_en(ch0_read_en) occurs twice: buffer and legacy consumer; both must be disabled','EDA_executed':False,'partial_source_preserved':True})+'\n')
support=W/'integration_support.py';s=support.read_text(encoding='utf-8');s=s.replace('R=Path(__file__).resolve().parents[3]', 'R=Path('+repr(str(R))+')');support.write_text(s,encoding='utf-8')
def edit(rel,fn):
 p=F/rel;s=p.read_bytes().decode('latin1').replace('\r\n','\n');new=fn(s);assert new!=s,rel;p.write_bytes(new.encode('latin1'))
def sub(s,pattern,replacement,count=1):
 s,n=re.subn(pattern,replacement,s);assert n==count,(pattern,n);return s
edit('rtl/ai7030_edif_top.v',lambda s:sub(sub(s,r'(input\s+sys_rst\s*,)',r'\1\n  input hdmi_ref_100m,'),r'(\.sys_rst\s*\(\s*sys_rst\s*\),)',r'\1\n  .hdmi_ref_100m(hdmi_ref_100m),'))
def peripheral(s):
 s=sub(s,r'(input\s+sys_rst\s*,)',r'\1\n  input hdmi_ref_100m,')
 s=sub(s,r'(mna_gp_ww_itf\s+cam\(\)\s*;)',r'\1\n  mna_gp_ww_itf cam_legacy();\n  mna_gp_ww_itf hdmi_csr();')
 s=sub(s,r'(\.cam\s*\()cam\.slave',r'\1cam_legacy.slave')
 start=s.index('frame_to_ps_largebuf frame_to_ps_inst0(');end=s.index('assign S_AXI_HP2_RDISSUECAP1_EN',start)
 block=s[start:end]
 block=block.replace('frame_to_ps_largebuf frame_to_ps_inst0(','frame_to_ps_largebuf #(.CANDIDATE_SCANOUT(1)) frame_to_ps_inst0(')
 for name in ['HDMI_CLK_P','HDMI_CLK_N','HDMI_TX_P','HDMI_TX_N']:
  block=sub(block,r'(\.'+name+r'\s*\()[^)]*(\))',r'\1\2')
 for name in ['arid','araddr','arlen','arsize','arburst','arlock','arcache','arprot','arqos','arvalid','rready']:
  block=sub(block,r'(\.m00_axi_'+name+r'\s*\()[^)]*(\))',r'\1\2')
 for name,value in [('arready',"1'b0"),('rid',"5'd0"),('rdata',"64'd0"),('rresp',"2'd0"),('rlast',"1'b0"),('rvalid',"1'b0")]:
  block=sub(block,r'(\.m00_axi_'+name+r'\s*\()[^)]*(\))',lambda m:m[1]+value+m[2])
 s=s[:start]+block+s[end:]
 addition='''
// Candidate exclusively owns HP2 AR/R. Camera AW/W/B connections above remain.
assign S_AXI_HP2_ARID=5'd0;
assign S_AXI_HP2_ARLOCK=2'd0;
assign S_AXI_HP2_ARCACHE=4'b0011;
assign S_AXI_HP2_ARPROT=3'd0;
assign S_AXI_HP2_ARQOS=4'b1111;
hdmi_cam_router #(.HDMI_BASE(32'h400b0000)) hdmi_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cam.slave),.camera(cam_legacy.master),.hdmi(hdmi_csr.master));
hdmi_board hdmi_display(
 .ref_100m(hdmi_ref_100m),.clock_reset(sys_rst),
 .csr_clk(gp_clk),.csr_resetn(~gp_clk_rst),.csr(hdmi_csr.slave),
 .mem_clk(hp_clk),.mem_resetn(~hp_clk_rst),
 .araddr(S_AXI_HP2_ARADDR),.arlen(S_AXI_HP2_ARLEN),.arsize(S_AXI_HP2_ARSIZE),.arburst(S_AXI_HP2_ARBURST),
 .arvalid(S_AXI_HP2_ARVALID),.arready(S_AXI_HP2_ARREADY),
 .rdata(S_AXI_HP2_RDATA),.rresp(S_AXI_HP2_RRESP),.rid(S_AXI_HP2_RID),.rlast(S_AXI_HP2_RLAST),
 .rvalid(S_AXI_HP2_RVALID),.rready(S_AXI_HP2_RREADY),
 .tmds_clk_p(HDMI_CLK_P),.tmds_clk_n(HDMI_CLK_N),.tmds_p(HDMI_TX_P),.tmds_n(HDMI_TX_N));
'''
 at=s.index(' assign S_AXI_HP2_RDISSUECAP1_EN') if ' assign S_AXI_HP2_RDISSUECAP1_EN' in s else s.index('assign S_AXI_HP2_RDISSUECAP1_EN')
 return s[:at]+addition+s[at:]
edit('rtl/ps_ai_peripheral.sv',peripheral)
def frame(s):
 s=sub(s,r'module\s+frame_to_ps_largebuf\s*\(', 'module frame_to_ps_largebuf #(parameter CANDIDATE_SCANOUT=0) (')
 for name,signal in [('read_req','ch0_read_req_sync'),('read_en','ch0_read_en'),('RD_START','rd_burst_req')]:
  s=sub(s,r'(\.'+name+r'\s*\()\s*'+signal+r'\s*(\))',lambda m:m[1]+"CANDIDATE_SCANOUT ? 1'b0 : "+signal+m[2],count=2 if name=='read_en' else 1)
 return s
edit('rtl/display/frame_to_ps_largebuf.v',frame)
old=F/'rtl/display/uihdmitx.v';shutil.copyfile(R/'FPGA/hdmi_candidate/rtl/display/uihdmitx.v',old)
def serdes(s):
 s=s.replace('reg int_rst;', '(* ASYNC_REG="TRUE" *) reg [2:0] reset_release;\nwire int_rst=reset_release[2];')
 return sub(s,r'always\s*@\(\*\)[\s\S]*?int_rst\s*<=\s*int_rst\s*;',
 "always @(posedge pclk or posedge txrst)\n    if(txrst) reset_release<=3'b111;\n    else reset_release<={reset_release[1:0],1'b0};")
edit('rtl/display/oserdese2_10to1.v',serdes)
dest=F/'rtl/hdmi_candidate';dest.mkdir(exist_ok=False)
names=['hdmi_scanout','hdmi_candidate_register_core','hdmi_register_bank','hdmi_candidate_core','hdmi_command_mailbox',
 'hdmi_scan_control','hdmi_axi_read','hdmi_stream_fifo','hdmi_pixel_scan']
for name in names:shutil.copyfile(R/'FPGA/hdmi_candidate/rtl'/(name+'.v'),dest/(name+'.v'))
for p in (R/'FPGA/hdmi_candidate/rtl/integration').glob('*'):shutil.copyfile(p,dest/p.name)
before=json.loads((E/'reference-rtl-before.json').read_text());after={p.relative_to(F/'rtl').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (F/'rtl').rglob('*') if p.is_file()}
changed=[n for n,h in before.items() if after[n]!=h];added=sorted(set(after)-set(before))
assert set(changed)=={'ai7030_edif_top.v','ps_ai_peripheral.sv','display/frame_to_ps_largebuf.v','display/uihdmitx.v','display/oserdese2_10to1.v'},changed
shutil.copytree(F/'rtl/hdmi_candidate',E/'integrated-rtl')
for rel in changed:
 p=E/'modified-reference-rtl'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(F/'rtl'/rel,p)
(E/'integration-wiring.json').write_text(json.dumps({'changed_reference_RTL':changed,'added_RTL':added,'all_other_RTL_unchanged':True,'after':after},indent=2)+'\n')
print(json.dumps({'changed_reference_RTL':changed,'added_RTL':len(added),'original_reference_untouched':True}))
