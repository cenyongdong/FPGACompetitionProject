"""Static review of the real vendor procedure body and visually checked schematic.
Never call replacement/reset procedures or modify installed databases.
"""
from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1'
P=R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r2'
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch'
viv=Path('D:/Xilinx/Vivado/2019.1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'path':str(p),'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None,'sha256':sha(p) if p.is_file() else None}
body=(P/'replace_7z030ai_file.body.tcl').read_text()
assert 'if {$vvd_version != "2018.3"}' in body
assert body.index('reset_database_to_default') < body.index('set Sitemap2_xml_wr')
assert not (P/'blocked-mutations.txt').read_bytes()
pairs=[
 ('Sitemap2.xml','data/parts/xilinx/zynq/devint/Sitemap2.xml'),
 ('unisim_comp.lib','scripts/rt/data/unisim_comp.lib'),
 ('unisim_comp.v','scripts/rt/data/unisim_comp.v'),
 ('zynq.lib','data/parts/xilinx/zynq/devint/zynq.lib'),
 ('zynq.rtd','data/parts/xilinx/zynq/devint/zynq.rtd'),
 ('zynq.xng','data/parts/xilinx/zynq/devint/zynq.xng'),
 ('zynq.padr','data/parts/xilinx/zynq/devint/zynq.padr'),
 ('xc7z030ai.paspd','data/parts/xilinx/zynq/devint/zynq/xc7z030/xc7z030.paspd'),
 ('unisim.btl','data/parts/xilinx/common/unisim.btl')]
inventory=[]
for src,dst in pairs:
 a=identity(kit/'030ai'/src);b=identity(viv/dst)
 inventory.append({'patch':a,'installed_target':b,'byte_identical_now':a['sha256']==b['sha256'] if b['exists'] else False})
allprocs=(P/'dependency-procedures.tcl').read_text()
reset=allprocs[allprocs.index('proc reset_database_to_default'):]
reset=reset[:reset.find('\nproc ',1)] if '\nproc ' in reset[1:] else reset
reset_paths=sorted(set(re.findall(r'\[format "%s/([^"\n]+)" \$vvd_path\]',reset)))
ps=R/'.local/hdmi-native-ps-20261015-r1/processing_system7_v5_5_atc.v'
t=ps.read_text();m=re.search(r'\bPS7\s+PS7_inst\s*\(',t);assert m
start=m.end();depth=1;end=start
while depth and end<len(t):
 depth+=(t[end]=='(')-(t[end]==')');end+=1
ports=re.findall(r'\.([A-Za-z_][A-Za-z0-9_]*)\s*\(',t[start:end-1])
port_info={'source':str(ps),'sha256':sha(ps),'line':t[:m.start()].count('\n')+1,
           'named_terminals':len(ports),'AI_IN':sum(v.startswith('AI_IN') for v in ports),
           'AI_OUT':sum(v.startswith('AI_OUT') for v in ports),
           'DEBUGDATA':sum(v.startswith('DEBUGDATA') for v in ports),
           'terminals':ports,'native_declaration_has_not_been_read':True,
           'root_cause_not_proven_by_count_alone':True}
(E/'PS7-callsite-review.json').write_text(json.dumps(port_info,indent=2)+'\n')
pin_rows=[
 {'signal':'ref_100m','schematic_net':'PL_100MHz','pin':'AC14','bank':12,'VCCO':3.3,'role':'100MHz oscillator G1; MRCC input'},
 {'signal':'HDMI_CLK','P':'AC17','N':'AC16','bank':12,'VCCO':3.3},
 {'signal':'HDMI_D0','P':'AA15','N':'AA14','bank':12,'VCCO':3.3},
 {'signal':'HDMI_D1','P':'Y16','N':'Y15','bank':12,'VCCO':3.3},
 {'signal':'HDMI_D2','P':'W16','N':'W15','bank':12,'VCCO':3.3},
 {'signal':'HDMI_HPD','pin':'AE16','bank':12,'VCCO':3.3,'role':'input after R353/R354 divider'},
 {'signal':'HDMI_DDC_SCL','pin':'AA17','bank':12,'VCCO':3.3,'role':'HDMIO_FSCL; MOS level translator, open-drain required'},
 {'signal':'HDMI_DDC_SDA','pin':'AB17','bank':12,'VCCO':3.3,'role':'HDMIO_FSDA; MOS level translator, open-drain required'},
 {'signal':'HDMI_CEC','pin':'AB16','bank':12,'VCCO':3.3,'role':'separate optional CEC net'},
 {'signal':'sys_rst / PL_KEY2','pin':'F8','bank':34,'VCCO':1.5,'role':'SW7: released low, pressed high; not PS power-on reset'}]
schematic=R/'Docs/开发板手册/JFMQL30TAI_LITE.pdf'
pins={'source':identity(schematic),'visually_reviewed_PDF_pages':[9,10,19,21,22],
      'schematic_sheet_labels':[9,10,23,25,26],
      'device_symbol':'U1 JFMQL30TAI','title_block_reuses_JFMQL100TAI_label':True,
      'rows':pin_rows,'live_measurement':False,
      '1080p60_warning_on_PDF_page_19':True,'not_automatically_switching_target_to_720p':True}
(E/'pin-contract.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'procedure_read_via_installed_Vivado_loader':True,'procedure_source_exit':0,
        'procedure_invoked':False,'version_guard':'exactly 2018.3; 2019.1 rejected by source condition',
        'replacement_pairs':inventory,'reset_helper_precedes_main_replacement':True,
        'reset_helper_target_paths_static':reset_paths,
        'fast_speed_source':identity(kit/'030ai/xc7z030ai_fast.paspd'),
        'Procise_database_paths_present_in_main_body':bool(re.search(r'PCPU7|Procise|procise',body)),
        'no_PS7_PCPU7_compatibility_claim':True,'no_global_database_write':True,
        'primary_copied_source_sha_equal':sha(kit/'all_src_files.tcl')==sha(R/'.local/hdmi-jfm-pin-review-20261015-r2/kit/ip_patch/all_src_files.tcl')}
(E/'replacement-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in (R/'.local/hdmi-jfm-pin-review-20261015-r1').glob('*.png'):
 shutil.copyfile(p,E/p.name)
print(json.dumps({'replacement_pairs':len(inventory),'existing_installed_targets':sum(x['installed_target']['exists'] for x in inventory),
 'same_hash_targets':sum(x['byte_identical_now'] for x in inventory),'reset_other_paths':len(reset_paths),
 'PS7_terminals':len(ports),'AI_terminals':port_info['AI_IN']+port_info['AI_OUT'],'pins':len(pin_rows)},ensure_ascii=True))
