"""Freeze actual reference-flow products and classify execution vs signoff."""
import jfm_build_support as s
from pathlib import Path
import json,hashlib,re,shutil,struct,zipfile
E=s.E;ref=s.W/'reference';run=ref/'fpai_demo_vivado.runs/impl_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((E/'implementation-only-r2/execution.json').read_text())
assert status['exit']==0 and not status['stopped_by_monitor']
out=E/'HELD-reference-products';out.mkdir(exist_ok=False)
products={}
def bit_header(data):
 pos=0
 def short():
  nonlocal pos
  n=struct.unpack_from('>H',data,pos)[0];pos+=2;return n
 n=short();pos+=n;assert short()==1;fields={}
 for key in b'abcd':
  assert data[pos]==key;pos+=1;n=short();fields[chr(key)]=data[pos:pos+n].rstrip(b'\0').decode('ascii');pos+=n
 assert data[pos]==ord('e');pos+=1;n=struct.unpack_from('>I',data,pos)[0];pos+=4;assert pos+n==len(data)
 return {'fields':fields,'payload_bytes':n,'file_bytes':len(data)}
for name in ['ai7030_edif_top.bit','ai7030_edif_top_disable_icap.bit','ai7030_edif_top_routed.dcp']:
 p=run/name;shutil.copyfile(p,out/name);assert sha(p)==sha(out/name)
 products[name]={'SHA':sha(p),'bytes':p.stat().st_size}
 if p.suffix=='.bit':products[name]['header']=bit_header(p.read_bytes())
assert 'Patched=DISABLE_ICAP' in products['ai7030_edif_top_disable_icap.bit']['header']['fields']['a']
s.dump(out/'identities.json',products)
(out/'README.md').write_text('''# HELD：原厂参考工程产物

这些是实际生成的参考工程位流/检查点，不包含新HDMI扫描候选，未下载。
setup/hold通过，但AI时钟模型存在2处最小周期违例，完整时序不通过；CDC和外部时序覆盖亦未签核。
禁止将工具exit0或Procise后处理完成视为上板验收。启动BOOT/SDK/模型/AI_Mate不改。
''',encoding='utf-8')
for name in ['procise_run_disable_icap.tcl','call_procise_disable_icap.bat']:
 shutil.copyfile(ref/name,out/name)
# Preserve every run's raw diagnostic products; artifacts above are directly accessible.
zip_path=E/'actual-run-products.zip';ids={}
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for p in (ref/'fpai_demo_vivado.runs').rglob('*'):
  if p.is_file() and p.suffix.lower() in {'.log','.vds','.rpt','.tcl','.bat','.xml','.dcp'}:
   n=p.relative_to(ref/'fpai_demo_vivado.runs').as_posix();ids[n]=sha(p);z.write(p,n)
with zipfile.ZipFile(zip_path) as z:
 for n,h in ids.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
s.dump(E/'actual-run-products-manifest.json',ids)
timing=(E/'implementation-only-r2/timing-summary.rpt').read_text(errors='replace')
match=re.search(r'^\s+(0\.030)\s+(0\.000)\s+0\s+200234\s+(0\.021)\s+(0\.000)\s+0\s+200137\s+(-0\.409)\s+(-0\.479)\s+2\s+60032\s*$',timing,re.M)
assert match and 'Timing constraints are not met.' in timing
rows=[]
for line in (E/'implementation-only-r2/CDC.rpt').read_text(errors='replace').splitlines():
 m=re.match(r'^(CDC-\d+)\s+(Critical|Warning|Info)\s+(\d+)\s+(.+)$',line)
 if m:rows.append({'rule':m[1],'severity':m[2],'report_count':int(m[3]),'description':m[4]})
clock_source=s.R/'Docs/26嵌赛开发/fpai_demo_fpga/rtl/edif/AI_Mate.edif'
lines=[]
with clock_source.open(encoding='utf-8',errors='replace') as f:
 for i,line in enumerate(f,1):
  if 405242<=i<=405390:lines.append(line)
(E/'AI-clock-trace/original-netlist-clock-excerpt.txt').write_text(''.join(lines),encoding='utf-8')
report={'original_factory_chain_execution_exit':0,'implementation_only_seconds':status['seconds'],
 'factory_reference_not_corrected_HDMI_candidate':True,'actual_raw_and_Procise_ICAP_bits_generated':True,
 'setup':{'WNS_ns':0.030,'TNS_ns':0.0,'failing_endpoints':0},
 'hold':{'WHS_ns':0.021,'THS_ns':0.0,'failing_endpoints':0},
 'minimum_period_gate':{'WPWS_ns':-0.409,'TPWS_ns':-0.479,'failing_endpoints':2,'passed':False,
 'clock_model':'clk_out1_AI_CORE_CLK_ST','period_ns':1.0,'required_period_ns':{'BUFG/I':1.409,'PLLE2_ADV/CLKOUT0':1.071}},
 'source_AI_Mate_SHA':sha(clock_source),'source_AI_Mate_changed':False,
 'actual_visible_BUFG_clock_load':'ai_core_clk_locked_reg/C only; physical hard-AI clock meaning not independently proven',
 'no_clock_register_pins':0,'unconstrained_internal_max_delay_pins':0,
 'input_no_delay_HIGH':11,'output_no_delay_HIGH':6,
 'CDC_summary':rows,'CDC_critical_report_entries':sum(x['report_count'] for x in rows if x['severity']=='Critical'),
 'CDC_counts_not_independent_silicon_fault_counts':True,'CDC_not_signed_off':True,
 'DRC_implementation_profile':'99 listed violations incl warnings/advisories, zero Error; only four GT checks disabled; two rule limits reached',
 'DRC_reopened_checkpoint_default_profile':'REQP-52/56 reappear as Error; DRC enable state is session context, not preserved in DCP',
 'MIG_CLK_REF_exception_preexists':True,'AI_clock_period_waiver_added':False,'AI_clock_frequency_changed':False,
 'full_system_signoff':False,'board_download':False,'BOOT_changed':False,'old_DATA_resumed':False}
s.dump(E/'result-review.json',report)
print(json.dumps({'execution_exit':0,'raw_and_ICAP_bits_generated':True,'full_timing_gate':False,
 'minimum_period_failed_endpoints':2,'CDC_critical_report_entries':report['CDC_critical_report_entries'],'frozen_run_products':len(ids)}))
