from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2]
V=R/'tools/pose-v1/evidence'
E=V/'hdmi-jfm-pin-review-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((E/'replacement-review.json').read_text(encoding='utf-8'))
checks=[]
for item in audit['replacement_pairs']:
 old=item['installed_target'];p=Path(old['path'])
 checks.append({'path':str(p),'before_sha256':old['sha256'],'after_sha256':sha(p),'equal':old['sha256']==sha(p)})
assert all(x['equal'] for x in checks)
(E/'installed-targets-after-review.json').write_text(json.dumps({'all_nine_equal':True,'targets':checks},indent=2)+'\n')
base=R/'Docs/26嵌赛开发/fpai_demo_fpga'
orig=json.loads((V/'hdmi-system-20261015-r1/original-manifest.json').read_text())
now={p.relative_to(base).as_posix():sha(p) for p in base.rglob('*') if p.is_file()}
assert orig==now
rtl=json.loads((V/'hdmi-bringup-20261015-r1/scanout-source-review.json').read_text())['sources']
assert all(sha(R/'FPGA/hdmi_candidate/rtl'/n)==h for n,h in rtl.items())
(E/'baseline-review.json').write_text(json.dumps({'all_297_reference_files_equal':True,'nine_scanout_RTL_equal_r6':True,'unchanged_loads_not_rerun':True},indent=2)+'\n')
link='[JFM与引脚补查](tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/REPORT.md)'
latest=('进一步按用户提示核对真实replace_7z030ai_file：严格限2018.3，先恢复多器件库再替换9项Vivado原语/器件文件；当前2019.1工程内只读入单文件仍报AI_IN端口不匹配，未改全局库或绕过版本检查。原理图确认AC14/100MHz、TMDS差分对，以及F8=1.5V/高有效PL_KEY2；IO直驱1080p60不可保证的限制保持。PS构建仍阻塞，未下载候选。')
changed=[]
def update(name,fn):
 p=R/name;b=p.read_bytes();s=b.decode('utf-8-sig');nl='\r\n' if '\r\n' in s else '\n'
 t=fn(s.replace('\r\n','\n'));assert t!=s.replace('\r\n','\n'),name
 before=E/'before'/name
 if not before.exists():before.parent.mkdir(parents=True,exist_ok=True);before.write_bytes(b)
 p.write_bytes(t.replace('\n',nl).encode('utf-8'))
 dest=E/'after'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 changed.append({'path':name,'before_sha256':sha(before),'after_sha256':sha(p)})
def progress(s):
 marker='共享模型最近实际验证：';end=s.index(marker)
 prefix=s[:end].rstrip()+' '+latest+' '+link+'。\n\n'
 s=prefix+s[end:]
 lines=s.splitlines()
 for i,v in enumerate(lines):
  if v.startswith('| HDMI |'):
   lines[i]='| HDMI | 扫描/TMDS常量、有限IP生成及AXI3路由/原生综合通过；引脚/电平和JFM函数体已核对 | PS7→PCPU7扩展端口不匹配；现有JFM替换函数严格限2018.3，当前2019.1单文件方案仍失败。完整PHY/CDC/实现与实屏待验，未下载候选/改BOOT；[恢复入口](FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md) |'
 return '\n'.join(lines)+'\n'
update('PROJECT-PROGRESS.md',progress)
update('REFERENCES.md',lambda s:s.replace('\n\n','\n\n2026-10-15本机资料补查：'+latest+' '+link+'、[Lite引脚契约](FPGA/hdmi_candidate/PIN-CONTRACT.md)、[真实JFM过程与版本边界](FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md)。原PDF第9/10/19/21/22页已渲染目视核验，图纸Sheet号与PDF页码分开记录。\n\n',1))
def difficult(s):
 lines=s.splitlines()
 for i,v in enumerate(lines):
  if v.startswith('| D05 |'):
   lines[i]='| D05 | HDMI实屏时序不支持；完整候选受PS扩展原语兼容阻塞 | 扫描、有限IP生成、AXI3路由/原生综合通过；原理图确认TMDS/参考时钟/按键极性；读到真实JFM替换函数 | 该函数严格限2018.3且涉及全局库，当前2019.1工程内单原语文件仍报AI_IN端口缺失；未改库/PS包/AI_Mate/BOOT，完整实现与实屏未验。需匹配版本30TAI配套；[补查证据](tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/REPORT.md) |'
 return '\n'.join(lines)+'\n'
update('DIFFICULTIES.md',difficult)
def done(s):
 key='### 工程内容总结';i=s.index(key)+len(key)
 s=s[:i]+'\n\n本批资料与隔离元数据核验：'+latest+' '+link+'。正常Vivado受保护Tcl加载器在只读拦截下成功读取过程定义，r2 3.141304秒exit0，未调用替换/恢复/hook。单PS7声明读取22.559951秒exit0但空顶层/端口0，端口契约明确不通过；实际PS包装RTL展开18.938109秒exit1、AI_IN端口不匹配/104 Errors。各60秒预算，失败保存停止。Poppler相关整页和放大图已目视检查，9项安装文件探针前后SHA同、297原参考及9扫描RTL同，无新板端动作。\n\n以下保留前批结果及其当时范围：'+s[i:]
 key='### 对后续开发的参考';i=s.index(key)+len(key)
 return s[:i]+'\n\n本批参考：库替换命令须读真实函数体及被调用的恢复过程，不能把“时序库”理解为仅时钟参数。版本条件与分支可达性分别核对，不绕过2018.3守卫套2019.1；可读取原语声明不等于实际端口绑定成功。器件封装球位和内部PS7原语端口是两层契约；F8按键是高有效请求，规范同步/AXI复位仍需验证。保留源码、stdout与stderr；旧版Tcl用英文路径，日志统一UTF-8。\n'+s[i:]
update('Done.md',done)
update('ARCHITECTURE-DISCUSSION-20261015.md',lambda s:s+'\n## 十四、用户补充JFM替换命令与Lite原理图后的核对\n\n'+latest+' '+link+'。本次提示按参考资料审查执行，未推导全局替换或新工具安装许可。真实过程读取、9目标身份、工程内元数据失败及完整相关原理图页面均保存。优先核对当前2019.1适用的正式30TAI配套；若只能用现有2018.3专用包，另行讨论隔离环境与官方构建路径，保留当前IP成果，不强制降级XCI。\n')
update('FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md',lambda s:s.replace('## 已实际闭合','## 用户补充资料后的最新核对\n\n'+latest+' 详见[JFM兼容核对](JFM-COMPATIBILITY-REVIEW.md)及[引脚契约](PIN-CONTRACT.md)。真实Tcl过程已通过正常加载器在只读拦截下读取；以下“未加载”是上一批结束时的状态。当前仍未执行replace/reset/hook，未更换工具或全局库；新探针失败与原生失败分别保留。\n\n## 已实际闭合',1))
update('FPGA/hdmi_candidate/RESUME.md',lambda s:s.replace('## 最新实际结果','## 最新资料与隔离元数据核对\n\n'+latest+' [JFM版本/影响与实际探针](JFM-COMPATIBILITY-REVIEW.md)、[Lite引脚/复位契约](PIN-CONTRACT.md)。单独原语读取的exit0只是空壳，实际PS包装仍展开失败；没有新硬件通过或下载。当前没有后台构建。\n\n## 最新实际结果',1))
update('FPGA/hdmi_candidate/INTEGRATION.md',lambda s:s.replace('## 模块、时钟和所有权','引脚和物理复位的新增核验见[PIN-CONTRACT.md](PIN-CONTRACT.md)：AC14独立100MHz，HDMI对/BANK12/3.3V；F8是BANK34/1.5V的PL_KEY2，松开低、按下高。规范复位同步与AXI协调仍待验证。JFM替换严格限2018.3、工程内单文件方案失败，详见[JFM兼容核对](JFM-COMPATIBILITY-REVIEW.md)。\n\n## 模块、时钟和所有权',1))
for name in ('FPGA/hdmi_candidate/PIN-CONTRACT.md','FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md'):
 p=R/name;dst=E/'after'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
 changed.append({'path':name,'before_sha256':None,'after_sha256':sha(p),'new_document':True})
(E/'documentation-revision.json').write_text(json.dumps({'changes':changed,'historical_manifests_not_rewritten':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
missing=[]
for name in [x['path'] for x in changed]+['tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/REPORT.md']:
 p=R/name
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if '://' not in target and not target.startswith('#') and not (p.parent/target.split('#')[0]).exists():
   missing.append({'source':name,'target':target})
assert not missing,missing
(E/'final-static-review.json').write_text(json.dumps({'Python_AST_files':len(scripts),'AST_passed':True,'missing_links':missing},indent=2)+'\n')
shutil.copyfile(Path(__file__),E/'finish_review.py')
print(json.dumps({'documents':len(changed),'all_9_installed_targets_equal':True,'AST_passed':True,'links_passed':True}))
