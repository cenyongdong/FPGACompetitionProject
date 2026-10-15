"""Read-only strict review of HDL model parameters and bus contracts.
Never rewrite prior rejected CONFIG reports or generate hardware products.
"""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3]
S=R/'Docs/26嵌赛开发/fpai_demo_fpga'
W=R/'.local/hdmi-bd-validation-20261015-r1/reference'
E=R/'tools/pose-v1/evidence/hdmi-bd-validation-20261015-r1'
P=R/'tools/pose-v1/evidence/hdmi-ip-revision-20261015-r1'
ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
def cfg(p):
 root=ET.parse(p)
 return {v.attrib['{'+ns['s']+'}referenceId']:v.text or '' for v in root.findall('.//s:configurableElementValue',ns)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
gate=json.loads((E/'post-validation-config-gate.json').read_text())
aliases={v['before']:v['after'] for v in gate['derived_role_renames']}
interface=[];model=[];parameters=[];added=[];used=[]
disabled=[]
for old in S.rglob('*.xci'):
 name=old.stem;newname=aliases.get(name,name)
 found=list(W.rglob(newname+'.xci'));assert len(found)==1,(name,found)
 new=found[0];a=cfg(old);b=cfg(new)
 disabled_clock=all(a.get('PARAM_VALUE.REG_'+v)!='11' and b.get('PARAM_VALUE.REG_'+v)!='11' for v in ('AW','AR','W','R','B'))
 for key,value in a.items():
  if key.startswith(('BUSIFPARAM_VALUE.','MODELPARAM_VALUE.','PARAM_VALUE.')) and b.get(key)!=value:
   item={'IP':name,'after_name':newname,'key':key,'before':value,'after':b.get(key)}
   if key=='PARAM_VALUE.Component_Name' and name in aliases and b.get(key)==newname:
    parameters.append(dict(item,classification='managed instance role rename; full BD connectivity/address preserved'))
   elif key=='BUSIFPARAM_VALUE.CLK2X.FREQ_HZ' and 'regslice' in name and disabled_clock:
    disabled.append(dict(item,classification='CLK2X is disabled for all REG_* values; verify component predicate'))
   elif key.startswith('MODELPARAM_VALUE.'):model.append(item)
   elif key.startswith('BUSIFPARAM_VALUE.'):interface.append(item)
   else:parameters.append(dict(item,classification='unclassified existing PARAM change'))
 newkeys={k:v for k,v in b.items() if k not in a and k.startswith(('PARAM_VALUE.','MODELPARAM_VALUE.','BUSIFPARAM_VALUE.'))}
 if newkeys:added.append({'IP':name,'new_keys':newkeys})
 used.append({'IP':name,'after_name':newname,'original':str(old),'updated':str(new),'before_sha':sha(old),'after_sha':sha(new)})
component=Path('D:/Xilinx/Vivado/2019.1/data/ip/xilinx/axi_register_slice_v2_1/component.xml')
c=ET.parse(component)
pred=[]
for v in c.iter():
 if v.tag.endswith('isEnabled') and any('CLK2X' in x or 'aclk2x' in x for x in v.attrib.values()):pred.append(dict(v.attrib))
assert len(pred)==2 and all('= 11' in ' '.join(v.values()) for v in pred)
result={'old_literal_CONFIG_gate_preserved':True,'post_BD_validation_required':True,
 'active_XCI_instances_reviewed':len(used),'HDL_model_parameter_differences':model,
 'active_bus_interface_differences':interface,'existing_PARAMETER_differences':parameters,
 'disabled_CLK2X_metadata_differences':disabled,'added_parameters_and_bus_metadata':added,
 'source_files':used,'CLK2X_enablement_primary_source':{'path':str(component),'sha256':sha(component),'predicates':pred},
 'generation_authorized_by_this_review':False}
(E/'HDL-and-bus-contract-review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'model_differences':len(model),'bus_differences':len(interface),'parameter_differences':parameters,
 'disabled_CLK2X_metadata':len(disabled),'instances_with_added_keys':len(added),
 'added_key_summary':[{v['IP']:list(v['new_keys'])} for v in added]},ensure_ascii=False))
