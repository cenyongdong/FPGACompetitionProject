"""Read-only inventory of original replace_ip_database targets; never applies it."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1'
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch';tool=Path('D:/vivado18.3/Vivado/2018.3')
text=(E/'parameters-drc/parameter-procedures.txt').read_text(encoding='utf-8')
body=text.split('PROCEDURE replace_ip_database\n',1)[1].split('PROCEDURE spd_replace\n',1)[0]
paths=re.findall(r'format "%s/(data/ip/xilinx/[^"\n]+)" \$vvd_path',body)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[]
for rel in paths:
 rel=rel.strip();dst=tool/rel;src=kit/'xilinx'/dst.name
 items.append({'relative':rel,'source':str(src),'source_exists':src.is_file(),'target_exists':dst.is_file(),
 'source_sha256':sha(src) if src.is_file() else None,'target_sha256':sha(dst) if dst.is_file() else None,
 'identical':sha(src)==sha(dst) if src.is_file() and dst.is_file() else None,
 'bytes':dst.stat().st_size if dst.is_file() else None})
assert len({x['relative'] for x in items})==len(items)
report={'operation':'read only; no replace_ip_database or library writes','targets':items,'target_count':len(items),
 'different_present':sum(x['identical'] is False for x in items),'missing_source':sum(not x['source_exists'] for x in items),
 'missing_target':sum(not x['target_exists'] for x in items)}
(E/'IP-library-readonly-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='targets'}))
