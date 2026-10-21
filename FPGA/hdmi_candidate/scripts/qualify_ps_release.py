"""Qualify native routed r26 results; retain only the two approved AI exceptions."""
from pathlib import Path
import argparse
import json
import re
import hashlib


def need(ok,message):
    if not ok:raise RuntimeError(message)


def main():
    p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('checkpoint',type=Path)
    p.add_argument('--route-stage',default='route-r8');p.add_argument('--ps-stage',default='ps-export-r2');p.add_argument('--synth-stage',default='synthesis-r3')
    p.add_argument('--opt-stage',default='opt-r8-r2');a=p.parse_args();e=a.evidence.resolve()
    reports=e/'qualified-r8'
    for stage in (a.ps_stage,a.synth_stage,a.opt_stage,a.route_stage,'final'):
        need(json.loads((e/(stage+'-execution.json')).read_text())['exit_code']==0,'Native stage failed: '+stage)
    need(a.checkpoint.is_file(),'Routed checkpoint missing')
    timing=(reports/'timing-final.rpt').read_text();lines=timing.splitlines()
    h=next(i for i,s in enumerate(lines) if 'WNS(ns)' in s and 'TNS(ns)' in s)
    v=next(s.split() for s in lines[h+1:] if re.match(r'^\s*-?\d+\.\d+\s',s))
    need(len(v)==12,'Inspect timing summary format')
    wns,tns,whs,ths=[float(v[i]) for i in (0,1,4,5)]
    need(wns>=0 and whs>=0 and tns==ths==0 and v[2]==v[6]=='0','Setup/hold not met')
    for pattern in (r'There are\s+0\s+pins that are not constrained for maximum delay\.',
                    r'There are\s+0\s+register/latch pins with no clock\.'):
        need(re.search(pattern,timing),'Internal timing/clock coverage incomplete')
    prefix='U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/'
    allowed={prefix+'clkout1_buf/I':(1.409,1.0,-0.409),prefix+'plle2_adv_inst/CLKOUT0':(1.071,1.0,-0.071)}
    exceptions=[]
    for s in lines:
        m=re.search(r'\s(-\d+\.\d+)\s+\S+\s+(\S+)\s*$',s)
        if not m or not re.match(r'^(Min Period|Max Period|Low Pulse Width|High Pulse Width)\s',s):continue
        values=tuple(float(x) for x in s.split() if re.fullmatch(r'-?\d+\.\d+',x))
        need(s.startswith('Min Period') and m[2] in allowed and values==allowed[m[2]],'New/changed pulse failure: '+s)
        exceptions.append(s)
    need(len(exceptions)==2 and int(v[10])==2,'Only two original AI exceptions permitted')
    need('VIOLATED' not in (reports/'bus-skew-final.rpt').read_text(),'Bus skew failed')
    route=(reports/'route-status-final.rpt').read_text()
    def route_count(label):
        match=re.search(r'# of '+re.escape(label)+r'\.+\s*:\s*(\d+)\s*:',route)
        need(match is not None,'Native route field missing: '+label)
        return int(match[1])
    routable=route_count('routable nets');fully_routed=route_count('fully routed nets')
    need(routable>0 and fully_routed==routable and route_count('nets with routing errors')==0,
         'Native routing is incomplete or has errors')
    drc=(reports/'drc-final.rpt').read_text()
    errors=re.findall(r'^(\S+#\d+)\s+Error\s*\n(.*?)(?=^\S+#\d+\s|\Z)',drc,re.M|re.S)
    legacy={'REQP-52':'rx_sdi_inst/SDI0/SDI/GTX_i/gtxe2_i','REQP-56':'rx_sdi_inst/gtxe2_common_0/gtxe2_common_i'}
    for name,body in errors:
        need(name.split('#')[0] in legacy and re.findall(r'\bcell\s+(\S+?):',body)==[legacy[name.split('#')[0]]],'New DRC error: '+name)
    facts=[s.split('\t') for s in (reports/'final-native-facts.tsv').read_text().splitlines()]
    need(['PART','xc7z030ffg676-2'] in facts,'Wrong actual target')
    need(any(s[0]=='PSRESET' and int(s[-1])>0 for s in facts),'PS reset output not connected to recorder')
    for kind,period in (('NEW_BUS',10),('NEW_META',5),('NEW_RAW',5),('OLD_BUS',10),('OLD_META',5),('READY',5)):
        rows=[s for s in facts if s[0]==kind]
        need(rows and all(abs(float(s[-2])-period)<0.001 and float(s[-1])>=0 for s in rows),'Missing/cut/failing path: '+kind)
    overlay=json.loads((e/'source-overlay.json').read_text())
    sources=[s for s in overlay['replacements'].values() if not s.endswith('ps_ai_processing_system7_0_0.v')]
    root=Path(__file__).resolve().parents[3]
    sources+=[str(root/'FPGA/hdmi_candidate/diagnostics/ps_release_witness.sv'),str(root/'FPGA/hdmi_candidate/constraints/ps_release_cdc.tcl')]
    sources+=[str(root/'FPGA/hdmi_candidate/constraints/ps_release_raw_flags_cdc.tcl')]
    sources+=[str(root/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl')]
    baseline_report=root/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/timing-final.rpt'
    ignored=baseline_report.read_text().split('User Ignored Path Table',1)[1].split('Unconstrained Path Table',1)[0]
    ignored_rows=[s.split() for s in ignored.splitlines()]
    gp='clk_out1_clk_wiz_0';rx='rx_sdi_inst/SDI0/SDI/GTX_i/gtxe2_i/RXOUTCLK'
    need(['(none)',gp,rx] in ignored_rows and ['(none)',rx,gp] in ignored_rows,
         'Original routed report does not confirm the restored factory GP/SDI scope')
    sources+=[str(root/'.local/hdmi-ps-release-20261020-r26/sources/ps_release_stub.v'),
              str(root/'.local/hdmi-ps-release-20261020-r26/sources/ps-managed-io.xdc'),
              str(root/'.local/hdmi-ps-release-20261020-r26/sources/ai_boot_witness_cdc.tcl')]
    ps_export=root/'.local/hdmi-ps-release-20261020-r26/ps-export.dcp'
    export_facts=[s.split('\t') for s in (e/'factory-PS-export-facts-r2.tsv').read_text().splitlines()]
    value=lambda k:next(s[1] for s in export_facts if s[0]==k)
    need(value('BASE_CELLS')==value('NEW_CELLS') and int(value('NEW_PORTS'))==int(value('BASE_PORTS'))+1,'PS export changed original cells/port contract')
    result=dict(bit_generation_prerequisite_pass=True,raw_timing_pass=False,WNS_ns=wns,WHS_ns=whs,TNS_ns=tns,THS_ns=ths,
        approved_AI_period_exceptions=exceptions,new_timing_exceptions=False,new_DRC_waivers=False,
        unconstrained_internal_endpoints=0,routable_nets=routable,fully_routed_nets=fully_routed,
        route_stage=a.route_stage,checkpoint=str(a.checkpoint.resolve()),
        source_sha256={s:hashlib.sha256(Path(s).read_bytes()).hexdigest() for s in sources},
        PS_base_checkpoint=value('BASE_CHECKPOINT'),PS_selected_checkpoint=str(ps_export),
        PS_selected_checkpoint_sha256=hashlib.sha256(ps_export.read_bytes()).hexdigest(),
        PS_export_script=str(e/(a.ps_stage+'.tcl')),
        superseded_PS_RTL_rebuild='ps-ooc.dcp is not used; qualified factory PS checkpoint is retained. Initial stub integration added a redundant PJTAG OBUF; top synthesis IO_BUFFER_TYPE corrects that integration error.',
        physical_facts='qualified-r8/final-native-facts.tsv',report_directory=str(reports),board_tested=False)
    (e/'qualification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('bit_generation_prerequisite_pass','WNS_ns','WHS_ns','raw_timing_pass')}))


if __name__=='__main__':main()
