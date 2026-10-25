"""Qualify native routed r26 results; retain only the two approved AI exceptions."""
from pathlib import Path
import argparse
import json
import re
import hashlib


def need(ok,message):
    if not ok:raise RuntimeError(message)


def native_exit(path):
    record=json.loads(path.read_text())
    return record.get('exit_code',record.get('native_exit'))


def main():
    p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('checkpoint',type=Path)
    p.add_argument('--route-stage',default='route-r8');p.add_argument('--ps-stage',default='ps-export-r2');p.add_argument('--synth-stage',default='synthesis-r3')
    p.add_argument('--opt-stage',default='opt-r8-r2')
    p.add_argument('--final-stage',default='final')
    p.add_argument('--report-dir',type=Path)
    p.add_argument('--source-overlay',type=Path)
    p.add_argument('--work',type=Path)
    p.add_argument('--source-support',type=Path)
    p.add_argument('--cdc-dir',type=Path)
    p.add_argument('--ps-evidence',type=Path)
    p.add_argument('--ps-export',type=Path)
    p.add_argument('--repository-root',type=Path,default=Path(__file__).resolve().parents[3])
    a=p.parse_args();e=a.evidence.resolve()
    code_root=Path(__file__).resolve().parents[3]
    root=a.repository_root.resolve()
    work=(a.work or root/'.local/hdmi-ps-release-20261020-r26').resolve()
    support=(a.source_support or work/'sources').resolve()
    cdc=(a.cdc_dir or root/'FPGA/hdmi_candidate/constraints').resolve()
    ps_evidence=(a.ps_evidence or e).resolve()
    reports=(a.report_dir or e/'qualified-r8').resolve()
    overlay_path=(a.source_overlay or e/'source-overlay.json').resolve()
    need(native_exit(ps_evidence/(a.ps_stage+'-execution.json'))==0,'Reused/native PS stage failed')
    for stage in (a.synth_stage,a.opt_stage,a.route_stage,a.final_stage):
        need(native_exit(e/(stage+'-execution.json'))==0,'Native stage failed: '+stage)
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
    overlay=json.loads(overlay_path.read_text())
    sources=[s for s in overlay['replacements'].values() if not s.endswith('ps_ai_processing_system7_0_0.v')]
    if overlay.get('additional_sources'):
        sources+=overlay['additional_sources']
        trace_facts=[s.split('\t') for s in (reports/'hp2-cycletrace-native-facts.tsv').read_text().splitlines()]
        need(any(s[0]=='TRACE_BRAM' and int(s[1])>0 for s in trace_facts),'Physical trace BRAM missing')
        for kind,period in [('META',5),('DESC',10),('RAW',5)]:
            need(any(s[0]=='TRACE_'+kind and int(s[1])>0 and abs(float(s[2])-period)<.001 and float(s[3])>=0
                     for s in trace_facts),'Physical trace path missing/cut/failing: '+kind)
        sources+=[str(code_root/'FPGA/hdmi_candidate/constraints'/name)
                  for name in ('hp2_cycle_trace_cdc.tcl','hp2_cycle_trace_validate.tcl')]
    sources+=[str(code_root/'FPGA/hdmi_candidate/diagnostics/ps_release_witness.sv'),str(cdc/'ps_release_cdc.tcl')]
    sources+=[str(cdc/'ps_release_raw_flags_cdc.tcl')]
    if (cdc/'hdmi_cdc.tcl').is_file():sources.append(str(cdc/'hdmi_cdc.tcl'))
    if (cdc/'ai_read_monitor_cdc.tcl').is_file():sources.append(str(cdc/'ai_read_monitor_cdc.tcl'))
    sources+=overlay.get('additional_constraint_sources',[])
    if overlay.get('protocol_checker'):
        protocol_facts=[s.split('\t') for s in (reports/'hp2-protocol-native-facts.tsv').read_text().splitlines()]
        for tag in ('PROTOCOL_BRAM','PROTOCOL_NATIVE_PRIMITIVES'):
            need(any(s[0]==tag and int(s[1])>0 for s in protocol_facts),'Physical protocol checker/capture absent: '+tag)
        for kind,period in [('META',5),('HELD',10),('RAW',5),('PSRESET',5)]:
            need(any(s[0]=='PROTOCOL_'+kind and int(s[1])>0 and abs(float(s[2])-period)<.001 and float(s[3])>=0
                     for s in protocol_facts),'Physical protocol path missing/cut/failing: '+kind)
        sources.append(overlay['protocol_checker']['xci'])
        if overlay['protocol_checker'].get('generation_script'):
            sources.append(overlay['protocol_checker']['generation_script'])
    sources+=[str(cdc/'ps_release_factory_clocks.tcl' if (cdc/'ps_release_factory_clocks.tcl').is_file()
                  else code_root/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl')]
    baseline_report=root/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/timing-final.rpt'
    ignored=baseline_report.read_text().split('User Ignored Path Table',1)[1].split('Unconstrained Path Table',1)[0]
    ignored_rows=[s.split() for s in ignored.splitlines()]
    gp='clk_out1_clk_wiz_0';rx='rx_sdi_inst/SDI0/SDI/GTX_i/gtxe2_i/RXOUTCLK'
    need(['(none)',gp,rx] in ignored_rows and ['(none)',rx,gp] in ignored_rows,
         'Original routed report does not confirm the restored factory GP/SDI scope')
    sources+=[str(support/'ps_release_stub.v'),str(support/'ps-managed-io.xdc'),
              str(cdc/'ai_boot_witness_cdc.tcl' if (cdc/'ai_boot_witness_cdc.tcl').is_file() else support/'ai_boot_witness_cdc.tcl')]
    ps_export=(a.ps_export or work/'ps-export.dcp').resolve()
    export_facts=[s.split('\t') for s in (ps_evidence/'factory-PS-export-facts-r2.tsv').read_text().splitlines()]
    value=lambda k:next(s[1] for s in export_facts if s[0]==k)
    need(value('BASE_CELLS')==value('NEW_CELLS') and int(value('NEW_PORTS'))==int(value('BASE_PORTS'))+1,'PS export changed original cells/port contract')
    if 'S01_inputs_held_zero' in overlay:
        rows=[s.split('\t') for s in (reports.parent/'source-isolation-native.tsv').read_text().splitlines()]
        need(len(rows)==27 and {s[1] for s in rows}==set(overlay['S01_inputs_held_zero'])
             and all(s[0]=='S01_ZERO' and s[2]=='GND' for s in rows),'Native S01 source isolation not proven')
    if overlay.get('S01_source_connected'):
        rows=[s.split('\t') for s in (reports.parent/'source-connected-native.tsv').read_text().splitlines()]
        connected=[s for s in rows if s[0]=='S01_CONNECTED']
        need({s[1] for s in connected}=={'ARVALID','ARADDR','RREADY'} and
             all(len(s)==3 and s[2] and s[2]!='GND' for s in connected),'Actual connected S01 not proven')
    result=dict(bit_generation_prerequisite_pass=True,raw_timing_pass=False,WNS_ns=wns,WHS_ns=whs,TNS_ns=tns,THS_ns=ths,
        approved_AI_period_exceptions=exceptions,new_timing_exceptions=False,new_DRC_waivers=False,
        unconstrained_internal_endpoints=0,routable_nets=routable,fully_routed_nets=fully_routed,
        route_stage=a.route_stage,checkpoint=str(a.checkpoint.resolve()),
        source_sha256={s:hashlib.sha256(Path(s).read_bytes()).hexdigest() for s in dict.fromkeys(sources)},
        source_overlay=str(overlay_path),protocol_checker=overlay.get('protocol_checker'),
        PS_base_checkpoint=value('BASE_CHECKPOINT'),PS_selected_checkpoint=str(ps_export),
        PS_selected_checkpoint_sha256=hashlib.sha256(ps_export.read_bytes()).hexdigest(),
        PS_export_script=str(ps_evidence/(a.ps_stage+'.tcl')),
        superseded_PS_RTL_rebuild='ps-ooc.dcp is not used; qualified factory PS checkpoint is retained. Initial stub integration added a redundant PJTAG OBUF; top synthesis IO_BUFFER_TYPE corrects that integration error.',
        physical_facts=str(reports/'final-native-facts.tsv'),report_directory=str(reports),board_tested=False)
    (e/'qualification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('bit_generation_prerequisite_pass','WNS_ns','WHS_ns','raw_timing_pass')}))


if __name__=='__main__':main()
