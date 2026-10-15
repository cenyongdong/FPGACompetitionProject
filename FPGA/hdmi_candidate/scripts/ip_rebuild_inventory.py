"""Static original XCI/BD/hook dependency inventory, never upgrade/generate IP."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3];S=R/'Docs/26嵌赛开发/fpai_demo_fpga'
E=R/'tools/pose-v1/evidence/hdmi-bringup-20261015-r1'
ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
rows=[]
for p in S.rglob('*.xci'):
 tree=ET.parse(p)
 for component in tree.findall('.//s:componentInstance',ns):
  c=component.find('s:componentRef',ns)
  rows.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
   'instance':component.findtext('s:instanceName',namespaces=ns),
   'core':{k.rsplit('}',1)[-1]:v for k,v in c.attrib.items()},
   'needs_generation_status':'not executed; tool IS_LOCKED/version status not yet queried'})
xpr=ET.parse(S/'fpai_demo_vivado.xpr');missing=[]
for f in xpr.findall('.//File'):
 raw=f.attrib['Path'];p=Path(raw.replace('$PPRDIR',S.as_posix()).replace('$PSRCDIR',(S/'fpai_demo_vivado.srcs').as_posix()))
 if not p.exists():
  candidate=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch/process_control'/p.name
  missing.append({'reference':raw,'same_name_in_local_kit':candidate.is_file(),'kit_path':str(candidate) if candidate.is_file() else None})
bd=S/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
info=json.loads(bd.read_text())['design']['design_info']
result={'static_only':True,'reference_BD':info,'XCI_components':rows,'missing_XPR_hooks':missing,
 'native_target':'JFMQL30TAI676H','existing_frontend':'D:/Xilinx/Vivado/2019.1/bin/vivado.bat',
 'IP_generation_executed':False,'IP_upgrade_executed':False,'hook_install_executed':False}
(E/'IP-rebuild-inventory.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'XCI_components':len(rows),'unique_cores':sorted(set(v['core']['name']+':'+v['core']['version'] for v in rows)),
 'missing_hooks':len(missing),'same_name_kit_files':sum(v['same_name_in_local_kit'] for v in missing),'BD_reference_tool':info['tool_version']},ensure_ascii=False))
