"""Read-only matching producer library/header/document evidence; no board actions."""
from pathlib import Path
import subprocess,json,hashlib,re
from html.parser import HTMLParser
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';assert not E.exists();E.mkdir();S=E/'sdk';S.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,name):
    p=subprocess.run([D,*args],capture_output=True);(E/(name+'.stdout')).write_bytes(p.stdout);(E/(name+'.stderr')).write_bytes(p.stderr);assert p.returncode==0,(name,p.stderr);return p.stdout
libs={'libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
for lib,h in libs.items():
    run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+lib,str(S/lib)],'copy-'+lib);assert sha(S/lib)==h
    run(['exec','FPAI','aarch64-linux-gnu-nm','-D','-S','-C','/usr/lib/aarch64-linux-gnu/'+lib],lib+'-symbols')
headers=['icraft-xrt/core/tensor.h','icraft-xrt/core/backend.h','icraft-xrt/core/session.h','icraft-xrt/dev/zg330_device.h','icraft-backends/zg330backend/zg330backend.h','icraft-xir/core/network.h']
identities={}
for name in headers:
    p=S/name;p.parent.mkdir(parents=True,exist_ok=True);run(['cp','-L','FPAI:/usr/include/'+name,str(p)],'header-'+name.replace('/','_'))
    win=Path('C:/Icraft/CLI v3.39.0/include')/name
    arm=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest();desktop=hashlib.sha256(win.read_bytes().replace(b'\r\n',b'\n')).hexdigest();assert arm==desktop
    identities[name]={'ARM_raw_sha256':sha(p),'normalized_sha256':arm,'Windows_normalized_equal':True}
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
docs=Path('C:/Icraft/CLI v3.39.0/docs');docids={}
names=['zg330backend/index.html','zg330backend/_cppapi/classicraft_1_1xrt_1_1zg330_1_1_z_g330_backend.html','xrt/_cppapi/classicraft_1_1xrt_1_1_tensor.html','xrt/_cppapi/classicraft_1_1xrt_1_1_z_g330_device.html','codegen/_cppapi/structicraft_1_1cg_1_1_code_gen_options.html']
for name in names:
    p=docs/name
    if not p.exists():continue
    parser=Text();parser.feed(p.read_text(encoding='utf-8'));text='\n'.join(x.strip() for x in parser.parts if x.strip());dest=E/('doc-'+p.stem+'.txt');dest.write_text(text,encoding='utf-8',newline='\n');docids[name]=sha(p)
inventory={}
for label,path in [('local_materials',Path('D:/Dowload from Chrome/嵌赛资料')),('sdk_docs',docs)]:
    candidates=[]
    for p in path.rglob('*'):
        if p.is_file() and (p.suffix.lower() in ('.v','.sv','.vhd','.vh','.zip','.7z','.gz','.xz','.pdf') or re.search('dma|axi|zg330|zhuge|sync|finish',p.name,re.I)):
            candidates.append({'path':p.relative_to(path).as_posix(),'bytes':p.stat().st_size})
    inventory[label]=candidates
(E/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(E/'audit.identity.json').write_text(json.dumps({'libraries':libs,'headers':identities,'docs_sha256':docids,'inventory_sha256':sha(E/'inventory.json'),'no_device_open':True,'no_Session':True,'no_NPU':True},indent=2)+'\n',encoding='utf-8',newline='\n');print('Producer audit captured',len(headers),'matching headers')

