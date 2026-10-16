"""Fresh reference release under a two-object user waiver; no programming."""
from pathlib import Path
import hashlib, json, re, shutil

R=Path(__file__).resolve().parents[3]
NAME='hdmi-board-reference-20261016-r1'
E=R/'tools/pose-v1/evidence'/NAME
W=R/'.local'/NAME
OLD=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
E.mkdir(exist_ok=False); W.mkdir(exist_ok=False)
docs=['Agents.md','PROJECT-PROGRESS.md','REFERENCES.md','DIFFICULTIES.md','Done.md',
      'FPGA/hdmi_candidate/AI-CLOCK-GATE.md','FPGA/hdmi_candidate/BOARD-PLAN.md',
      'FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/INTEGRATION.md']
ids={}
for rel in docs:
    p=R/rel; dest=E/'before'/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    content=p.read_text(encoding='utf-8-sig')
    if rel=='Agents.md': content=re.sub(r'密码：[^，。\r\n]+','密码：[REDACTED]',content)
    dest.write_text(content,encoding='utf-8')
    ids[rel]={'original_sha256':sha(p),'snapshot_sha256':sha(dest),'credential_redacted':rel=='Agents.md'}
(E/'documentation-before.json').write_text(json.dumps(ids,indent=2)+'\n')
release=E/'released-reference-products';release.mkdir()
expected={
 'ai7030_edif_top.bit':'5a435937c5a0be8a3bce0db77555bd85e67c4b4ebf450c5afbd662e779e2fb50',
 'ai7030_edif_top_disable_icap.bit':'ab9af4b8679a8f4bbe958d4dadbc78b81156da4a3b5a67c6510c9d1269befb78'}
for name,digest in expected.items():
    source=OLD/'HELD-reference-products'/name
    assert sha(source)==digest, 'Source identity changed'
    shutil.copyfile(source,release/name)
    assert sha(release/name)==digest
record={'date':'2026-10-16','authorization':'User explicitly approved waiver and real-board validation',
 'requested_label':'已知原厂安全占位时钟',
 'classification':'User-accepted legacy factory clock-model exception; physical safety/placeholder semantics not independently proved',
 'clock':'clk_out1_AI_CORE_CLK_ST','period_ns':1.0,
 'checks':[{'pin_suffix':'AI_CORE_CLK/inst/clkout1_buf/I','type':'Min Period','required_ns':1.409,'slack_ns':-0.409},
           {'pin_suffix':'AI_CORE_CLK/inst/plle2_adv_inst/CLKOUT0','type':'Min Period','required_ns':1.071,'slack_ns':-0.071}],
 'raw_timing_pass':False,'min_period_HELD_released':True,'full_system_signoff':False,
 'reference_only_HDMI_candidate_integrated':False,'products_sha256':expected,
 'board_programmed':False,'persistent_BOOT_modification_authorized':False,
 'other_gates':['fresh chain and device identity','safe runtime reconfiguration and rollback','CDC and external timing classification'],
 'no_changes':['raw reports','timing libraries','clock frequencies','AI_Mate','SDK','models','BOOT']}
(E/'release-authorization.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
transport=(R/'.local/shared-stability-transport-20261015-r2/secure_transport.py').read_text(encoding='utf-8')
transport=transport.replace("ROOT = Path(__file__).resolve().parents[2]",'ROOT = Path('+repr(str(R))+')')
transport=transport.replace("REMOTE = '/tmp/wifi-pose-shared-stability-20261015-r2/'", "REMOTE = '/tmp/"+NAME+"/'")
(W/'secure_transport.py').write_text(transport,encoding='utf-8')
shutil.copyfile(Path(__file__),E/'prepare_board_release.py')
print(json.dumps({'evidence':str(E),'reference_release_sha_match':True,'programmed':False}))
