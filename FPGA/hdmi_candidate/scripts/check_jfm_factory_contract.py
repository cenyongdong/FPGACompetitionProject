"""Check original root XCI configuration and immutable source contracts after generation."""
import jfm_build_support as s
import xml.etree.ElementTree as ET,json,hashlib
source=s.R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=s.W/'reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def params(p):
 out={}
 for n in ET.parse(p).getroot().iter():
  if n.tag.split('}')[-1]=='configurableElementValue':
   name=next((v for k,v in n.attrib.items() if k.split('}')[-1]=='referenceId'),None)
   if name and not name.startswith(('RUNTIME_PARAM.','PROJECT_PARAM.')):out[name]=n.text
 return out
items=[];diff=[]
for p in source.rglob('*.xci'):
 rel=p.relative_to(source);now=ref/rel;before=params(p);after=params(now)
 changes={k:{'before':before.get(k),'after':after.get(k)} for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
 items.append({'path':rel.as_posix(),'parameter_count':len(before),'differences':changes})
 if changes:diff.append(rel.as_posix())
immutable=[p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in {'.prj','.edf','.edif','.v','.sv','.vhd','.xdc'}]
changed=[p.relative_to(source).as_posix() for p in immutable if sha(p)!=sha(ref/p.relative_to(source))]
s.dump(s.E/'generated-contract-review.json',{'root_XCI':items,'XCI_with_differences':diff,'original_RTL_DDR_PRJ_EDIF_XDC_changes':changed,
 'IP_revision_upgrade':False,'BD_generated_internal_names_not_asserted_as_external_identity':True})
assert not diff,diff
assert not changed,changed
print(json.dumps({'original_XCI_contracts':len(items),'immutable_RTL_DDR_EDIF_XDC':len(immutable),'all_pass':True}))
