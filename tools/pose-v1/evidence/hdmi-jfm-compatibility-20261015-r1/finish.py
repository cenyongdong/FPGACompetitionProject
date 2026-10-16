from pathlib import Path
import ast, hashlib, html, json, re, shutil

R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
V = R / 'tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p):return p.read_text(encoding='utf-8-sig')
# Verify protected original inputs and the previously accepted RTL; no reruns of passed loads.
original=json.loads((R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json').read_text(encoding='utf-8'))
ref=R/'Docs/26嵌赛开发/fpai_demo_fpga'
bad=[n for n,h in original.items() if sha(ref/n)!=h];assert not bad,bad
old=json.loads((R/'tools/pose-v1/evidence/hdmi-split-20261015-r1/scanout-RTL-identity-consistency.json').read_text(encoding='utf-8'))
for item in old:assert sha(R/'FPGA/hdmi_candidate/rtl'/item['source'])==item['current_sha'],item['source']
pairs=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text(encoding='utf-8'))['replacement_pairs']
targets=[]
for pair in pairs:
 p=Path(pair['installed_target']['path']);actual=sha(p);expected=pair['installed_target']['sha256']
 assert actual==expected,str(p)
 targets.append({'path':str(p),'before_sha256':expected,'after_sha256':actual,'equal':True})
dump(E/'baseline-review.json',{'all_297_reference_files_equal':len(original)==297,'nine_scanout_RTL_unchanged':len(old)==9,
 'all_nine_installed_targets_unchanged':True,'installed_targets':targets,
 'board_not_connected_this_batch':True,'BOOT_SDK_model_not_rechecked_on_board_this_batch':True})

(E/'REPORT.md').write_text('''# 30TAI配套迁移到Vivado2019.1的评估与备用下载状态

2026-10-15，Windows，工作目录D:/FPGACompetitionProject。按用户顺序先评估2019.1；用户另确认全部官方资料已本地保存且没有该版本配套。实际结论：常规RTL/IP已有成果保持，但用现有资料不能完成可验证的完整2019.1迁移。不是理论上不可移植的证明，未逆向受保护数据库。

## 已执行与通过标准

现有Vivado2019.1在新目录中只展开输入直连输出的小锚点模块，使标准器件库可查询，未加载或重跑已失败的实际PS。get_lib_cells/get_lib_pins读取到PS7，28.899712秒/60秒预算、exit0；[完整执行](../hdmi-vivado2019-library-20261015-r1/execution.json)、[原始位引脚](../hdmi-vivado2019-library-20261015-r1/builtin-PS7-pins.txt)。通过标准仅为真实库元数据读取并与安装Liberty逐项核对，不是PS综合、迁移、时序或硬件通过。

| 比较项 | 实际结果 |
|---|---|
| 2019.1运行库PS7 | 3305个位引脚，规范化方向后与安装zynq.lib逐项一致 |
| 030ai配套PS7 | 7213个位引脚，公共同名引脚方向无差异 |
| 原PS调用的AI_端口 | 3868个，在运行库全部缺失，在030ai Liberty全部存在 |
| 九项030ai替换源 | 八项Xlx受保护文件头；zynq.lib为可读文本 |
| 原生Procise PCPU7 | 此前实际PS展开失败保持，换前端不能直接证明已解决 |

[逐项名称、方向与格式证据](migration-contract-review.json)。命名实参4527项与位引脚数不是同一计数口径，不能直接比大小；本结论按AI_名称逐项核对。单份Liberty或伪造同名黑盒不能补齐物理资源/时序/位流契约。全库二进制移植无2019.1重建源与正式验证依据，未作为修复执行。此前工程内单文件读取的实际PS失败保留，未自动重跑。

## 本地/官方资料核对及范围修正

原始JFM_Kits.zip实际1,239,868,855字节、3829条目，[归档SHA](local-kit-archive-identity.json)；关键脚本与已解压目录一致，[ZIP关键条目](local-kit-archive-review.json)。本地默认rg会忽略部分归档，本次用明确路径读取，不能因默认检索遗漏就说没有原包。

用户补充之前，已只读获取官方公共索引：Procise目录列出的32494工具与本机相同，索引将完整FPGA教程/源码获取指向企业方；Icraft参考入口亦已读取。索引/搜索看不到兼容包不是全球不存在的证明。用户确认资料完整后停止继续寻找该版本，改为迁移评估。浏览器正文读取超时与初次网络连接失败原样保留；后续在获准限制外执行的正常TLS、固定主机、限时/限大小HTTPS读取成功。原始HTML与[全部链接](all-observed-portal-links.json)保留，未联系企业、登录或提交信息，未将第三方教程作为兼容性技术依据。

## 备用下载及待执行范围

用户已允许无法可靠迁移时下载2018.3。核对[AMD官方归档](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2018-3.html)的完整HLx包18.97 GB；Lab Edition仅编程/调试，不能替代本次前端。官方账户下载入口网页实际返回会话未建立，Codex打开浏览器返回queued；已请求用户登录或告知已有本机安装包路径。[下载状态](download-status.json)。没有取得安装包，没有安装/启动下载器，也未提交账户或许可证表单。

具体下载落点、独立2018.3安装及库修改范围、原2018.3工程恢复、每步通过/停止条件见[版本方案](../../../..//FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md)。安装/库替换仍是待确认阶段；目前没有工具环境变更。即使2018.3前端通过，仍须闭合30TAI专用网表到Procise的真实PS绑定，FMP100通用迁移脚本不能直接套用。

## 证据保护与停止

本次分析器两次失败分别因BIDIR/inout术语未规范化、误以为补丁源名等于安装目标名，原失败版本和说明保存；修复分析器后仅重新分析已有文本，没有重跑PS或板端负载。生产扫描RTL九份、原参考297文件、2019.1九项安装目标SHA重新核对一致；源码/文档前后值、静态检查与新证据清单另存，不回写旧封存清单。

没有板端连接、候选下载、BOOT/模型/SDK/AI_Mate/PS变更或重启。无完整候选位流；旧DATA仍独立暂停。查询超时/异常则保存并结束进程树，未自动重试；本次实际查询未超时。最终进程盘点与封存结果见completion-review.json。
'''.replace('../../../..//FPGA','../../../../FPGA'),encoding='utf-8')

sources=E/'source-snapshots';sources.mkdir(exist_ok=False)
for name in ['read_vendor_portal.py','fetch_vendor_index.py','inspect_2019_ps_library.py','review_2019_migration.py']:
 shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/name,sources/name)
shutil.copyfile(Path(__file__),E/'finish.py')
print(json.dumps({'documents_updated_in_previous_phase':9,'baseline_files':len(original),'scanout_RTL':len(old),'global_targets_unchanged':len(targets)},ensure_ascii=True))
