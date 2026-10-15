"""Read-only inventory of reference build dependencies; never generates IP."""
from pathlib import Path
import collections,hashlib,json,re,xml.etree.ElementTree as ET
from pypdf import PdfReader
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-resume-20261015-r1'
S=R/'Docs/26嵌赛开发/fpai_demo_fpga'
manifest=[]
for f in ET.parse(S/'fpai_demo_vivado.xpr').findall('.//File'):
 raw=f.attrib['Path'];p=Path(raw.replace('$PPRDIR',S.as_posix()).replace('$PSRCDIR',(S/'fpai_demo_vivado.srcs').as_posix()))
 manifest.append({'reference':raw,'exists':p.is_file(),'resolved':str(p),
                  'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None})
roots=[S,R/'FPGA',Path('D:/Dowload from Chrome/嵌赛资料/Icraft/参考实现')]
files=[]
for root in roots:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower() in ('.edif','.edf','.xci','.fpr','.fdc','.xdc','.xpr','.bit','.bin','.dcp','.pdc'):
   files.append({'path':str(p),'bytes':p.stat().st_size,'extension':p.suffix.lower()})
audit={'reference_project':str(S/'fpai_demo_vivado.xpr'),'filesets':manifest,
       'missing_count':sum(not f['exists'] for f in manifest),'inventory':files}
(E/'reference-build-inventory.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
doc=Path('C:/FudanMicro/Procise/documents/Procise原语手册.pdf')
pages=[]
for i,p in enumerate(PdfReader(doc).pages):
 text=p.extract_text() or ''
 if any(k in text for k in ('PAR2SER','BUFOUT','TMDS','HDMI','742.5','1.25Gb')):
  pages.append({'page':i+1,'text':text})
(E/'native-primitive-excerpts.json').write_text(json.dumps({'source':str(doc),'sha256':hashlib.sha256(doc.read_bytes()).hexdigest(),'pages':pages},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
edif=R/'tools/pose-v1/evidence/hdmi-candidate-procise-scanout-20261015-r1/returned-project/rundir/hdmi_scanout.edif'
counts=collections.Counter(re.findall(r'\(cellRef ([^\s\)]+)',edif.read_text()))
(E/'native-synthesis-cells.json').write_text(json.dumps(counts,indent=2)+'\n')
print(json.dumps({'reference_files':len(manifest),'missing':audit['missing_count'],'inventory_files':len(files),
                  'primitive_excerpt_pages':[p['page'] for p in pages], 'native_cells':counts},ensure_ascii=False))
