"""Read a fixed public vendor index; no login, upload, install or settings edits."""
from pathlib import Path
import json,re,time,urllib.request
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
assert not (E/'portal-fetch-elevated.json').exists()
url='https://university-program.fdwmy.com/'
t=time.monotonic()
try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as f:
        data=f.read(2_000_001);status=f.status;final=f.url;ctype=f.headers.get('Content-Type')
    (E/'portal-index-elevated.html').write_bytes(data)
    result={'url':url,'final_url':final,'status':status,'bytes':len(data),'content_type':ctype,
            'script_src':re.findall(r'<script[^>]+src=[\'"]([^\'"]+)',data.decode('utf-8',errors='replace'))}
except Exception as ex:
    result={'url':url,'error':type(ex).__name__+': '+str(ex)}
result.update(seconds=time.monotonic()-t,tls_verification_disabled=False,external_mutation=False)
(E/'portal-fetch-elevated.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
