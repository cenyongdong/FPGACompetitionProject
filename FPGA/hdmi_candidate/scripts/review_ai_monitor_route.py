"""Review actual observer route, keeping the two existing AI model exceptions."""
from pathlib import Path
import json,re,hashlib,collections
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r2'
P=E/'monitor-v2-reports';W=R/'.local/hdmi-live-20261017-r1/reference'
assert not (P/'review.json').exists()
for name in ['monitor-v2-route','monitor-v2-reports']:
 assert json.loads((E/name/'execution.json').read_text())['exit']==0
sources=json.loads((E/'monitor-v2-constraints/review.json').read_text())['source_sha256']
for rel,expected in sources.items():assert hashlib.sha256((W/rel).read_bytes()).hexdigest()==expected,rel
text=(P/'timing-summary.rpt').read_text();lines=text.splitlines()
idx=next(i for i,line in enumerate(lines) if line.startswith('    WNS(ns)'));values=lines[idx+2].split();assert len(values)==12
wns,tns,whs,ths,wpws,tpws=[float(values[i]) for i in [0,1,4,5,8,9]]
assert wns>=0 and whs>=0 and tns==ths==0
assert values[2]==values[6]=='0' and values[10]=='2'
assert wpws==-0.409 and tpws==-0.479
assert 'There are 0 register/latch pins with no clock.' in text
assert 'There are 0 pins that are not constrained for maximum delay.' in text
native=W/'fpai_demo_vivado.runs/impl_ai_monitor_v2'
pulse=[line for line in (native/'ai7030_edif_top_timing_summary_routed.rpt').read_text().splitlines() if line.startswith('Min Period') and re.search(r'\s-0\.',line)]
assert len(pulse)==2
prefix='U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/'
for endpoint,required,slack in [('clkout1_buf/I','1.409','-0.409'),('plle2_adv_inst/CLKOUT0','1.071','-0.071')]:
 match=[line for line in pulse if line.endswith(prefix+endpoint)]
 assert len(match)==1 and required in match[0] and slack in match[0]
drc=(native/'ai7030_edif_top_drc_routed.rpt').read_text()
assert not re.findall(r'^\S+#\d+ Error$',drc,re.M)
assert 'REQP-1580#' not in drc and 'UTLZ-1#' not in drc
assert 'The following rules are disabled: REQP-44, REQP-46, REQP-52, REQP-56' in drc
reopened=(P/'DRC-reopened-default-profile.rpt').read_text()
assert re.findall(r'^(\S+#\d+) Error$',reopened,re.M)==['REQP-52#1','REQP-56#1']
status=(P/'route-status.rpt').read_text()
assert re.search(r'# of nets with routing errors\.+\s*:\s*0\s*:',status)
assert 'VIOLATED' not in (P/'bus-skew.rpt').read_text()
bounds=(P/'snapshot-routed-bounds.txt').read_text().splitlines()
assert len(bounds)==3
for row,name,expected in zip(bounds,['observer','command','response'],[10.,5.,10.]):
 assert row.startswith(name+'|')
 assert float(re.search(r'requirement=([\d.]+)',row)[1])==expected
 assert float(re.search(r'slack=([\d.-]+)',row)[1])>=0
 for kind in ['setup','hold']:
  if name=='observer':assert 'VIOLATED' not in (P/('observer-'+kind+'.rpt')).read_text()
 for row_ce in (P/('snapshot-'+name+'-CE.txt')).read_text().splitlines():
  assert float(re.search(r'requirement=([\d.]+)',row_ce)[1])==expected
  assert float(re.search(r'slack=([\d.-]+)',row_ce)[1])>=0
command_ce=(P/'snapshot-command-CE.txt').read_text().splitlines();assert len(command_ce)==96
for kind in ['setup','hold']:assert 'VIOLATED' not in (P/('HDMI-'+kind+'.rpt')).read_text()
obsrows=[line for line in (P/'observer-CDC.rpt').read_text().splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s',line)]
obscount=dict(collections.Counter(re.search(r'CDC-\d+',line)[0] for line in obsrows))
bits=json.loads((E/'monitor-v2-constraints/review.json').read_text())['bits']
assert obscount=={'CDC-3':2,'CDC-15':bits,'CDC-9':2},obscount
assert not any('Critical' in line for line in obsrows)
allrows=[line for line in (P/'CDC.rpt').read_text().splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s',line)]
hdmirows=[line for line in allrows if '/hdmi_display/' in line]
for line in hdmirows:
 if re.search(r'\bCDC-1\s',line):assert '/mailbox/payload_hold_reg' in line
 else:assert re.search(r'\bCDC-(3|6|10|12|15)\s',line),line
physical=(P/'HDMI-clock-physical.txt').read_text()
assert physical.count('|OSERDESE2|')==8
assert physical.count('/CLK|serial_raw')==physical.count('/CLKDIV|pixel_clk')==8
assert '|BUFIO|' in physical and '|BUFR|' in physical and '|MMCME2_ADV|' in physical
review={'bit_generation_prerequisite_pass':True,'scope':'offline diagnostic candidate only; no whole-system or board acceptance',
 'global_setup_WNS_ns':wns,'global_hold_WHS_ns':whs,'TNS_ns':tns,'THS_ns':ths,
 'raw_timing_pass':False,'unchanged_user_exception_MinPeriod_rows':pulse,
 'snapshot_bounds':bounds,'HDMI_command_CE_paths':len(command_ce),'observer_CDC_row_counts':obscount,
 'HDMI_CDC_row_counts':dict(collections.Counter(re.search(r'CDC-\d+',line)[0] for line in hdmirows)),
 'factory_DRC_profile_errors':0,'reopened_default_profile_errors_retained':['REQP-52#1','REQP-56#1'],
 'warnings_retained':True,'new_timing_or_DRC_waiver':False,'new_BOOT_or_reboot_authorized':False,
 'source_sha256':sources}
(P/'review.json').write_text(json.dumps(review,indent=2))
print(json.dumps({k:v for k,v in review.items() if k!='source_sha256'},indent=2))
