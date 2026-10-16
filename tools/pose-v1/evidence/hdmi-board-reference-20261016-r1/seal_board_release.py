"""Check previous seal, syntax, new links and documentation revisions, then seal."""
from pathlib import Path
import ast,json,hashlib,re,shutil
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1';OLD=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old_ids=json.loads((OLD/'files.sha256.json').read_text())
assert all(sha(OLD/name)==digest for name,digest in old_ids.items()),'Previous sealed evidence changed'
before=json.loads((E/'documentation-before.json').read_text())
rel='ARCHITECTURE-DISCUSSION-20261015.md';source=R/rel;dest=E/'before'/rel;shutil.copyfile(source,dest)
before[rel]={'original_sha256':sha(source),'snapshot_sha256':sha(dest),'credential_redacted':False,'snapshot_timing':'Late capture, immediately before first mutation in this batch'}
(E/'documentation-before.json').write_text(json.dumps(before,indent=2)+'\n')
with source.open('a',encoding='utf-8') as f:
 f.write('''

## 20. 两处最小周期定点豁免与参考载荷复现（2026-10-16）

用户明确解除AI时钟模型两处Min Period的HELD，允许受控板测；原始WPWS−0.409ns报告保留，“已知原厂安全占位时钟”作为用户接受的例外标签，未独立验证安全/占位语义。参考产物已发布。JTAG下载器重连后实际扫链通过，jfmql30/0x9372c093/part0；BOOT和六SDK身份保持。

进一步逐字节比较证明新Procise参考bit的完整配置载荷与现所选BOOT的PL载荷完全相同；原BOOT离线封装全文件复现。换入新bit的试制BOOT只有9个映像名称字节不同、PL分区0字节变化，原严格门检失败保留。这是构建链复现证据，不含HDMI修复：未下载、未改启动区、未重启、未完成新的实时/实屏验收。

下一有效对象仍是已批准的HDMI整机候选；共享模型与PS/NPU资源结构保持。新CSR、独立时钟、HP2读所有权和stop/drain依现行集成契约核对，当前在线隔离证据不足，不通过猜测寄存器或重复加载同配置宣称验证完成。旧DATA调查继续暂停。[现行发布与恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)、[本轮完整证据](tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/REPORT.md)。
''')
done=R/'Done.md';text=done.read_text(encoding='utf-8');text=text.replace('2026-10-16定点豁免与板测准备：','2026-10-16本轮初次预检记录（下载器随后已重连，现行结论见上）：',1);done.write_text(text,encoding='utf-8')
docs=list(before)+['FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md']
revisions={};new_broken=[]
def broken(rel,content):
 out=set()
 for target in re.findall(r'\]\(([^)]+)\)',content):
  target=target.strip('<>').split('#',1)[0]
  if not target or re.match(r'(https?|app|codex|plugin):',target):continue
  target=re.sub(r':\d+$','',target)
  p=Path(target)
  if not p.is_absolute():p=(R/rel).parent/target
  if not p.exists():out.add(target)
 return out
for rel in docs:
 p=R/rel;out=E/'after'/rel;out.parent.mkdir(parents=True,exist_ok=True)
 content=p.read_text(encoding='utf-8-sig')
 old=(E/'before'/rel).read_text(encoding='utf-8') if rel in before else ''
 new_broken.extend({'file':rel,'target':x} for x in broken(rel,content)-broken(rel,old))
 if rel=='Agents.md':content=re.sub(r'密码：[^，。\r\n]+','密码：[REDACTED]',content)
 out.write_text(content,encoding='utf-8')
 revisions[rel]={'before':before.get(rel),'after_original_sha256':sha(p),'after_snapshot_sha256':sha(out)}
assert not new_broken,new_broken
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
executed_tcl=list(E.rglob('*.tcl'))
assert not any(re.search(r'^\s*program_bit\s',p.read_text(errors='replace'),re.M) for p in executed_tcl)
(E/'documentation-revision.json').write_text(json.dumps(revisions,indent=2)+'\n')
status=json.loads((E/'current-status.json').read_text())
completion={'previous_sealed_files_checked':len(old_ids),'previous_seal_pass':True,'current_docs':len(docs),
 'Python_AST_files_checked':len(scripts),'new_broken_local_links':new_broken,'executed_program_bit_commands':0,
 'documentation_credential_snapshots_redacted':True,'actual_scope':status,
 'resource_cleanup':'All this-batch subprocesses waited; unrelated SSH PID28848 preserved; see final-host-process-inventory.json'}
(E/'completion-review.json').write_text(json.dumps(completion,indent=2)+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
ids={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file() and p.name!='files.sha256.json'}
(E/'files.sha256.json').write_text(json.dumps(ids,indent=2)+'\n')
assert all(sha(E/name)==digest for name,digest in ids.items())
print(json.dumps({'sealed_files':len(ids),'old_sealed_files_verified':len(old_ids),'documents':len(docs),'Python_AST':len(scripts),'new_broken_links':0,'programmed':False}))
