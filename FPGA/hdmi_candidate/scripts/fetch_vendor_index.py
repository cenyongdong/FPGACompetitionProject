"""Bounded, read-only public vendor index retrieval from observed links/forms.
Fixed host; no login, uploads, software installation or global settings edits.
"""
from pathlib import Path
import concurrent.futures,json,sys,time,urllib.parse,urllib.request
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
name=sys.argv[1];assert name in ('indexes','details','reference','install-metadata','implementation')
request_file=E/(name+'.requests.json')
urls=json.loads(request_file.read_text(encoding='utf-8'))
assert 1<=len(urls)<=4
for url in urls:
 p=urllib.parse.urlsplit(url)
 assert p.scheme=='https' and p.hostname=='university-program.fdwmy.com' and not p.username and not p.password
target=E/name;target.mkdir(exist_ok=False)
def fetch(item):
 i,url=item;t=time.monotonic()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as f:
   data=f.read(3_000_001);status=f.status;final=f.url;ctype=f.headers.get('Content-Type')
  (target/(str(i)+'.html')).write_bytes(data)
  return {'index':i,'url':url,'final_url':final,'status':status,'bytes':len(data),'content_type':ctype,'seconds':time.monotonic()-t}
 except Exception as ex:return {'index':i,'url':url,'error':type(ex).__name__+': '+str(ex),'seconds':time.monotonic()-t}
with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:results=list(pool.map(fetch,enumerate(urls)))
(target/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=True))
