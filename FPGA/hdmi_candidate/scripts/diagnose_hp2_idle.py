"""Focused HP2 diagnostics; native logs, one run record, no board activity."""
from pathlib import Path
import argparse,json,os,re,subprocess,time

R=Path(__file__).resolve().parents[3]
W=R/'.local/hdmi-hp2-idle-20261018-r10'
E=R/'tools/pose-v1/evidence/hdmi-hp2-idle-20261018-r10'
REF=R/'.local/hdmi-live-20261018-r9/reference'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')
TAG=''

def run(name,args):
    name+=TAG
    E.mkdir(exist_ok=True);W.mkdir(exist_ok=True)
    logfile=E/(name+'.stdout.txt');errfile=E/(name+'.stderr.txt')
    if logfile.exists():raise RuntimeError('Existing stage evidence; choose a new stage name')
    env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64';env['XILINX_VIVADO']=str(V.parent)
    for key in list(env):
        if key.startswith('RDI_'):env.pop(key)
    t=time.monotonic()
    with logfile.open('xb') as out,errfile.open('xb') as err:
        p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        while True:
            try:code=p.wait(timeout=30);break
            except subprocess.TimeoutExpired:
                print(json.dumps(dict(stage=name,pid=p.pid,seconds=round(time.monotonic()-t,1),still_running=True,stdout_bytes=logfile.stat().st_size,action='inspect/monitor original process; no automatic kill')),flush=True)
    row=dict(stage=name,args=[str(a) for a in args],exit=code,seconds=time.monotonic()-t,board=False)
    with (E/'execution.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
    if code:raise RuntimeError('Native stage failed: '+name+'; original logs retained')
    return logfile.read_text(errors='replace')

def vivado(name,body):
    W.mkdir(exist_ok=True);p=W/(name+'.tcl');p.write_text(body,encoding='utf-8')
    return run(name,[str(V/'vivado.bat'),'-mode','batch','-nojournal','-log',str(E/(name+'.vivado.log')),'-source',str(p)])

def main():
    global TAG
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['help','extract','extract-controls','extract-baseline','rtl','gates','run-rtl']);parser.add_argument('--tag',default='');parser.add_argument('--reset-cycles',type=int,default=12);parser.add_argument('--netlist',default='actual_hp2_routed.v');parser.add_argument('--invert-cut-ar',action='store_true');a=parser.parse_args()
    TAG=('-'+a.tag) if a.tag else ''
    if a.action=='run-rtl':
        output=run('simulate-rtl-r2',[str(V/'xsim.bat'),'hp2_idle_rtl','--tclbatch','run.tcl'])
        if 'HP2_IDLE_PASS' not in output or 'Fatal:' in output:raise RuntimeError('Testbench failed; raw simulator output retained')
        print(output[-1800:]);return
    if a.action=='help':
        vivado('write-verilog-help','help write_verilog\nexit\n');return
    if a.action=='extract-baseline':
        body=r'''if {[catch {
set root {U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4}
open_checkpoint {@@REF@@/fpai_demo_vivado.runs/impl_read_v3r9/ai7030_edif_top_opt.dcp}
write_verilog -mode funcsim -write_all_overrides -cell [get_cells $root] -rename_top actual_hp2_routed {@@WORK@@/actual_hp2_opt.v}
close_design
open_checkpoint {@@REF@@/fpai_demo_vivado.runs/impl_read_v3r9/ai7030_edif_top_routed.dcp}
set f [open {@@OUT@@/AR-boundary-context.txt} w]
foreach tail {S00_AXI_arvalid S00_AXI_arready S01_AXI_arvalid S01_AXI_arready} {
 set pin [get_pins [format {%s/%s} $root $tail]]
 puts $f "BOUNDARY|$pin"
 foreach p [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin]] {
  if {[get_property DIRECTION $p] eq "OUT"} {
   set c [get_cells -of_objects $p]
   puts $f "DRIVER|$p|[get_property REF_NAME $c]|INIT=[get_property INIT $c]"
   foreach q [get_pins -of_objects $c -filter {DIRECTION == IN}] {
    puts $f "DRIVER_INPUT|$q|NET=[get_nets -segments -of_objects $q]"
    foreach up [get_pins -leaf -of_objects [get_nets -segments -of_objects $q]] {
     if {[get_property DIRECTION $up] eq "OUT"} {puts $f "UPSTREAM|$up|[get_property REF_NAME [get_cells -of_objects $up]]|INIT=[get_property INIT [get_cells -of_objects $up]]"}
    }
   }
  }
 }
}
close $f
close_design
puts "HP2_OPT_AND_BOUNDARY_CONTEXT_EXTRACTED"
} msg]} {puts $msg;puts $::errorInfo;exit 1}
exit
'''.replace('@@REF@@',REF.as_posix()).replace('@@WORK@@',W.as_posix()).replace('@@OUT@@',E.as_posix())
        vivado('extract-opt-and-context',body);return
    if a.action=='extract-controls':
        body=r'''if {[catch {
open_checkpoint {@@REF@@/fpai_demo_vivado.runs/impl_read_v3r9/ai7030_edif_top_routed.dcp}
set root {U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4}
set reader {U0_ps_ai_peripheral/hdmi_display/scanout/core/core/reader}
write_verilog -mode funcsim -write_all_overrides -cell [get_cells $root] -rename_top actual_hp2_routed {@@WORK@@/actual_hp2_routed_explicit.v}
write_verilog -mode funcsim -write_all_overrides -cell [get_cells $reader] -rename_top actual_hdmi_reader {@@WORK@@/actual_hdmi_reader.v}
report_property -all -file {@@OUT@@/reader-ARVALID-register.txt} [get_cells [format {%s/FSM_onehot_state_reg[2]} $reader]]
report_property -all -file {@@OUT@@/reader-ARVALID-reset-pin.txt} [get_pins [format {%s/FSM_onehot_state_reg[2]/CLR} $reader]]
set f [open {@@OUT@@/reader-reset-driver.txt} w]
foreach tail {C CE CLR D Q} {
 set pin [get_pins -quiet [format {%s/FSM_onehot_state_reg[2]/%s} $reader $tail]]
 puts $f "PIN|$pin|NET=[get_nets -segments -of_objects $pin]"
 foreach p [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin]] {
  if {[get_property DIRECTION $p] eq "OUT"} {puts $f "DRIVER|$p|[get_property REF_NAME [get_cells -of_objects $p]]"}
 }
}
close $f
set lut [get_cells [format {%s/s00_couplers/s00_regslice/inst/ar.ar_pipe/m_valid_i_i_1__1} $root]]
report_property -all -file {@@OUT@@/routed-AR-LUT.txt} $lut
foreach p [get_pins -of_objects $lut] {
 report_property -all -file [format {@@OUT@@/routed-AR-LUT-%s.txt} [get_property REF_PIN_NAME $p]] $p
}
close_design
open_checkpoint {@@REF@@/fpai_demo_vivado.runs/synth_read_v3r9/ai7030_edif_top.dcp}
write_verilog -mode funcsim -write_all_overrides -cell [get_cells $root] -rename_top actual_hp2_routed {@@WORK@@/actual_hp2_synth.v}
close_design
puts "HP2_EXPLICIT_AND_SYNTH_EXTRACTED"
} msg]} {puts $msg;puts $::errorInfo;exit 1}
exit
'''.replace('@@REF@@',REF.as_posix()).replace('@@WORK@@',W.as_posix()).replace('@@OUT@@',E.as_posix())
        vivado('extract-control-and-synth',body);return
    if a.action=='extract':
        dcp=REF/'fpai_demo_vivado.runs/impl_read_v3r9/ai7030_edif_top_routed.dcp'
        dst=W/'actual_hp2_routed.v'
        body='''if {[catch {
set usage [help write_verilog]
puts $usage
if {[string first {-cell} $usage]<0} {error "Installed tool does not advertise cell extraction"}
open_checkpoint {%s}
set cell [get_cells {U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4}]
if {[llength $cell]!=1} {error "Actual HP2 interconnect missing"}
write_verilog -mode funcsim -cell $cell -rename_top actual_hp2_routed {%s}
set f [open {%s} w]
foreach tail {S01_AXI_arvalid S01_AXI_arready S00_AXI_arid[0] S00_AXI_arid[4] M00_AXI_arid[5] M00_AXI_rid[5] S00_AXI_rvalid S01_AXI_rvalid} {
 set pin [get_pins -quiet [format {%%s/%%s} $cell $tail]]
 puts $f "PIN|$pin"
 foreach q [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin]] {
  if {[get_property DIRECTION $q] eq "OUT"} {puts $f "DRIVER|$q|[get_property REF_NAME [get_cells -of_objects $q]]"}
 }
}
close $f
close_design
puts "ACTUAL_HP2_ROUTED_EXTRACTED"
} msg]} {puts $msg;puts $::errorInfo;exit 1}
exit
'''%(dcp.as_posix(),dst.as_posix(),(E/'routed-control-connections.txt').as_posix())
        vivado('extract-routed-hp2',body);return
    # Source model and physical netlist share one testbench and input stimulus.
    tb=R/'FPGA/hdmi_candidate/sim/tb_hp2_idle.sv'
    if not tb.exists():raise RuntimeError('Focused testbench not yet prepared')
    bd=REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    full=(bd/'synth/ps_ai.v').read_text()
    module=re.search(r'\bmodule ps_ai_axi_interconnect_3_0\b(.*?)endmodule',full,re.S).group()
    ports=re.findall(r'^\s*(input|output)\s*(?:wire\s*)?(\[[^\]]+\])?\s*(\w+)\s*;',module,re.M)
    driven={'S00_AXI_araddr','S00_AXI_arid','S00_AXI_arlen','S00_AXI_arsize','S00_AXI_arburst','S00_AXI_arvalid','S00_AXI_rready',
            'M00_AXI_arready','M00_AXI_rid','M00_AXI_rdata','M00_AXI_rresp','M00_AXI_rlast','M00_AXI_rvalid',
            'S01_AXI_araddr','S01_AXI_arlen','S01_AXI_arsize','S01_AXI_arburst','S01_AXI_arvalid','S01_AXI_rready'}
    top='ps_ai_axi_interconnect_3_0' if a.action=='rtl' else 'actual_hp2_routed'
    text=tb.read_text().replace('// PORTS','\n'.join('wire '+width+' '+name+';' for _,width,name in ports))
    if a.action=='gates':text='`define PHYSICAL_HP2\n'+text
    if a.tag.startswith('trace'):text='`define TRACE_HP2\n'+text
    text=text.replace('repeat(12)@(negedge clk);\n      #0.75;rstn=1;',f'repeat({a.reset_cycles})@(negedge clk);\n      #0.75;rstn=1;')
    if a.invert_cut_ar:
        # Counterfactual probe only: never modify the actual netlist or RTL.
        text=text.replace('assign S00_AXI_arvalid=ai_valid;','assign S00_AXI_arvalid=~ai_valid;')
        text=text.replace('if(S00_AXI_arvalid &&','if(ai_valid &&')
    text=text.replace('// DUT',top+' fabric('+','.join('.'+name+'('+name+')' for _,_,name in ports)+');')
    text=text.replace('// INPUTS','\n'.join('assign '+name+' = '+('clk' if name.endswith('ACLK') else 'rstn' if name.endswith('ARESETN') else "'0")+';' for direction,_,name in ports if direction=='input' and name not in driven))
    expanded=W/('tb_'+a.action+TAG+'.sv');expanded.write_text(text,encoding='utf-8')
    files=[]
    if a.action=='rtl':
        for stem in ['axi_infrastructure_v1_1_vl_rfs','generic_baseblocks_v2_1_vl_rfs','axi_crossbar_v2_1_vl_rfs','axi_register_slice_v2_1_vl_rfs','axi_data_fifo_v2_1_vl_rfs']:
            found=list((bd/'ipshared').rglob(stem+'.v'))
            if len(found)!=1:raise RuntimeError('Ambiguous actual dependency: '+stem)
            files.extend(found)
        files += [bd/'ip'/name/'synth'/(name+'.v') for name in ['ps_ai_xbar_4','ps_ai_s00_regslice_1','ps_ai_s01_regslice_0','ps_ai_m00_regslice_0']]
        files.append(bd/'synth/ps_ai.v')
        includes=sorted({str(p.parent) for p in (bd/'ipshared').rglob('*.vh')})
        cmd=[str(V/'xvlog.bat')]
        for inc in includes:cmd+=['-i',inc]
        run('compile-rtl',cmd+[str(p) for p in files])
    else:
        run('compile-gates',[str(V/'xvlog.bat'),str(V.parent/'data/verilog/src/glbl.v'),str(W/a.netlist)])
    src=REF/'rtl/hdmi_candidate'
    run('compile-tb-'+a.action,[str(V/'xvlog.bat'),'--sv',str(src/'hdmi_command_mailbox.v'),str(src/'hdmi_scan_control.v'),str(src/'hdmi_axi_read.v'),str(src/'hdmi_candidate_core.v'),str(expanded)])
    snapshot='hp2_idle_'+a.action+TAG.replace('-','_')
    run('elaborate-'+a.action,[str(V/'xelab.bat'),'tb_hp2_idle',*(['glbl'] if a.action=='gates' else []),'--timescale','1ns/1ps','--mt','2','-L','unisims_ver','-L','secureip','--snapshot',snapshot])
    script=W/'run.tcl';script.write_text('run all\nquit\n')
    output=run('simulate-'+a.action,[str(V/'xsim.bat'),snapshot,'--tclbatch','run.tcl'])
    if 'HP2_IDLE_PASS' not in output or 'Fatal:' in output:raise RuntimeError('Testbench failed; no physical or SDK action')
    print(output[-1800:])

if __name__=='__main__':main()
