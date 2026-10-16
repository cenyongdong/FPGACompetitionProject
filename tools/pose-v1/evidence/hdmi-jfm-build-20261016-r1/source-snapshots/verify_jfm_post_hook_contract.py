"""Recheck configuration after the factory MIG source adaptation, not byte-gate RTL."""
import jfm_build_support as s
import xml.etree.ElementTree as ET,hashlib,json
src=s.R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=s.W/'reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parameters(p):
 d={}
 for n in ET.parse(p).getroot().iter():
  if n.tag.split('}')[-1]=='configurableElementValue':
   name=next((v for k,v in n.attrib.items() if k.split('}')[-1]=='referenceId'),None)
   if name and not name.startswith(('RUNTIME_PARAM.','PROJECT_PARAM.')):d[name]=n.text
 return d
ips=[];diff=[]
for p in src.rglob('*.xci'):
 rel=p.relative_to(src);a=parameters(p);b=parameters(ref/rel)
 delta={k:{'original':a.get(k),'current':b.get(k)} for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
 ips.append({'path':rel.as_posix(),'parameter_count':len(a),'differences':delta})
 if delta:diff.append(rel.as_posix())
prj=[{'path':p.relative_to(src).as_posix(),'same_SHA':sha(p)==sha(ref/p.relative_to(src))} for p in src.rglob('*.prj')]
bd=[{'path':p.relative_to(src).as_posix(),'same_SHA':sha(p)==sha(ref/p.relative_to(src))} for p in src.rglob('*.bd')]
result={'XCI':ips,'DDR_PRJ':prj,'BD':bd,'gate_pass':not diff and all(x['same_SHA'] for x in prj+bd),
 'factory_generated_MIG_RTL_and_XDC_intentionally_adapted':True,'no_claim_of_generated_RTL_byte_identity':True}
s.dump(s.E/'post-factory-IP-contract.json',result)
assert result['gate_pass'],result
print(json.dumps({'original_XCI_contracts':len(ips),'DDR_PRJ':len(prj),'BD':len(bd),'post_hook_gate_pass':True}))
