"""Apply the authorized, backed-up 32 exact factory IP library replacements."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';W=R/'.local/hdmi-jfm-build-20261016-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (E/'IP-library-apply.json').exists(),'Do not reapply a completed or partially failed batch'
proc=subprocess.run(['tasklist','/FI','IMAGENAME eq vivado.exe','/FO','CSV','/NH'],capture_output=True,check=True)
assert b'vivado.exe' not in proc.stdout.lower(),'Close Vivado before library replacement'
review=json.loads((E/'IP-library-backup-manifest.json').read_text(encoding='utf-8'))
assert len(review['targets'])==32
for x in review['targets']:
 target=Path('D:/vivado18.3/Vivado/2018.3')/x['relative'];src=W/'reference/ip_patch/xilinx'/target.name
 assert target.resolve().is_relative_to(Path('D:/vivado18.3/Vivado/2018.3/data/ip/xilinx').resolve())
 assert sha(target)==x['target_sha256']==sha(E/'IP-library-backup'/x['relative'])
 assert sha(src)==x['source_sha256']
result={'start':time.time(),'method':'Exact factory source/target file copies; 32-file allowlist and independent verified backups',
 'installation':'D:/vivado18.3/Vivado/2018.3','attempted':[],'complete':False,'no_other_installation_targets':True}
dump(E/'IP-library-apply.json',result)
try:
 for x in review['targets']:
  dst=Path('D:/vivado18.3/Vivado/2018.3')/x['relative'];src=W/'reference/ip_patch/xilinx'/dst.name
  shutil.copyfile(src,dst);actual=sha(dst)
  result['attempted'].append({'relative':x['relative'],'before_SHA':x['target_sha256'],'after_SHA':actual,'source_SHA':x['source_sha256']})
  dump(E/'IP-library-apply.json',result);assert actual==x['source_sha256']
 result['complete']=True;result['end']=time.time();dump(E/'IP-library-apply.json',result)
except BaseException as ex:
 result['error']=str(ex);dump(E/'IP-library-apply.json',result);raise
print(json.dumps({'exact_library_files_applied':len(result['attempted']),'all_SHA_match':True,'complete':True}))
