"""Fresh factory-flow qualification project and exact 32-file backup (no patch)."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';W=R/'.local/hdmi-jfm-build-20261016-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
docs=['Agents.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','Done.md','REFERENCES.md','ARCHITECTURE-DISCUSSION-20261015.md',
 'FPGA/hdmi_candidate/ROUTE2-AUDIT.md','FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/INTEGRATION.md']
import re
identities=[]
for rel in docs:
 p=R/rel;dst=E/'before'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if rel=='Agents.md':dst.write_text(re.sub(r'(密码\s*[:：]\s*)[^，。\s]+',r'\1<REDACTED>',p.read_text(encoding='utf-8-sig')),encoding='utf-8')
 else:shutil.copyfile(p,dst)
 identities.append({'path':rel,'original_SHA':sha(p),'snapshot_SHA':sha(dst),'redacted':rel=='Agents.md'})
dump(E/'documentation-before-identities.json',identities)
manifest=json.loads((R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json').read_text())
source=R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=W/'reference'
for n,h in manifest.items():assert sha(source/n)==h,n
shutil.copytree(source,ref)
for n,h in manifest.items():assert sha(ref/n)==h,n
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch'
shutil.copytree(kit,ref/'ip_patch')
kitids={p.relative_to(kit).as_posix():sha(p) for p in kit.rglob('*') if p.is_file()}
for n,h in kitids.items():assert sha(ref/'ip_patch'/n)==h,n
dump(E/'factory-kit-identity.json',{'files':kitids,'total_bytes':sum(p.stat().st_size for p in kit.rglob('*') if p.is_file())})
old=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1'
lib=json.loads((old/'IP-library-readonly-inventory.json').read_text(encoding='utf-8'))
for x in lib['targets']:
 target=Path('D:/vivado18.3/Vivado/2018.3')/x['relative'];dst=E/'IP-library-backup'/x['relative'];dst.parent.mkdir(parents=True,exist_ok=True)
 assert sha(target)==x['target_sha256'];assert sha(Path(x['source']))==x['source_sha256']
 shutil.copyfile(target,dst);assert sha(dst)==x['target_sha256']
dump(E/'IP-library-backup-manifest.json',lib)
dump(E/'scope.json',{'authorization':'User approved scheme and autonomous local-evidence decisions on 2026-10-16',
 'sequence':['factory flow qualification','integrate validated HDMI candidate','implementation and Procise postprocess gates','authorized board validation only after safety gates'],
 '32_IP_patch_files_backed_up':True,'change_speed':False,'GT_checks_factory_030ai_only':['REQP-44','REQP-46','REQP-52','REQP-56'],
 'factory_project_original_files':len(manifest),'no_full_tool_clone':True,'BOOT_or_reboot':False,
 'initial_monitor_seconds':180,'absolute_stage_ceiling_seconds':1800,'max_threads':2,'parallel_runs':1,
 'timeout_action':'Assess owned progress and resources; bounded continuation, preserve decisions; stop actual errors/identity mismatch/OOM',
 'work':str(W),'tool':'D:/vivado18.3/Vivado/2018.3','libraries_not_yet_patched':True})
print(json.dumps({'reference_files':len(manifest),'kit_files':len(kitids),'backups':32,'library_patch_executed':False}),flush=True)
