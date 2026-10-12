"""Archive completed scope and point project roots at its immutable evidence."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def insert_after_title(rel,text):
    p=root/rel;s=p.read_text(encoding='utf-8');assert 'PLDDR-POSITION-RESULTS-20261010' not in s
    first,rest=s.split('\n',1);p.write_text(first+'\n\n'+text.strip()+'\n'+rest,encoding='utf-8',newline='\n')
insert_after_title('Agents.md','''- 公开PL DDR容量／较高来源位置独立对照本批结束（2026-10-10）：audit bfdacec4…4ef0ba5零Tensor，DefaultMemManager公开ADDR4096／4294963200字节、空块，匹配ARM成功分配路径为地址管理／小型元数据，非整个4GiB物理容量证明。position-r1 f375b781…408f16b／manifest29759437…2e1b464，403包94来源；主fbf330d7…cb8702d与旧typed f1c88850…218f2d9逐位保持，Host107／12注册59600与旧异常读取身份复用，未新模型。Native／ARM位置12拒绝＋冻结字节8拒绝／101模式202指纹过。96MiB SDK自有占位起点4096、read/write/copy0，真实192类型／分布源100667392／100697664、padding32@100697632／64对齐／合法窗口／不重叠；无VPU动态100对94.25189ms＋VPU100对19800.40012ms合2388000FP32全字节正确，初始各1对读回／对间0、index1–100全唯一。公开块0→1→4→0，全部自有块归还。VPU229capture含1参数集227图像1空LAST／41557字节，227解码ID与实际PTS、提交归还／正常drain／两STREAMOFF／join后SDK销毁过，NoInput合成不计模型吞吐。规整0、资源前普通单位24／策略16，内核事件同（跨shell/Python仅旧jffs2版权符号完整单行转义白名单），未清缓存／重启／CMA／BOOT变化，所有项目程序／端口／代理会话关闭。最终MemAvailable698728KiB/CmaFree130360／普通单位24仅现场，apt后台任务不擅改。无模型Session／NPU forward，旧坏块未复现／根因未修；约96MiB源不等于模型精确104MiB，NPU生产及运行时差异仍待。ADR_25、PLDDR-POSITION-RESULTS/NEXT和plddr-position-20261010-r1 completion/next-checkpoint为当前入口。下一原混合Engine无视频三窗→103仅准备未实施，不猜等待/cache/私有映射／零拷贝或重跑旧失败；管理粗估83/100保持，稳定103／长期／HDMI待，旧当前为历史。''')
insert_after_title('Done.md','''## 2026-10-10：公开分配器核验与较高来源动态／VPU对照完成

### 工程内容总结

独立审计确认默认PL DDR公开管理器／ADDR4096起点／4294963200声明容量及空分配列表；实际ARM成功分配路径保存地址／长度并申请小型对象，不据此证明整个4GiB物理容量。新position-r1 f375b781…408f16b／manifest29759437…2e1b464，403包94来源，原主及旧typed ELF／原载荷／SDK保持，Host107／12注册59600明确身份复用。Native／ARM各12位置拒绝、原8字节拒绝及101组模式过。

96MiB SDK自有占位无数据访问，两源100667392／100697664、真实192类型和全有效分布／64对齐／非重叠；动态100对94.25189ms＋VPU100对19800.40012ms合2388000 FP32逐位正确。227合成图像／实际PTS／解码ID、41557字节、正常LAST／提交归还／两STREAMOFF通过，join后SDK销毁，公共分配块0→1→4→0。规整0、内核事件同、全项目测试与代理连接结束。最终MemAvailable698728KiB／CmaFree130360／普通单位24仅现场，非泄漏或永久启动可靠性证明。

### 对后续开发的参考

没有模型Session／NPU前向，旧192坏块未复现、根因未修；约96MiBSDK来源不能替代真实模型104MiB／NPU生产路径验收。本批定位完成不提高全项目粗估83/100。下一原Engine无视频负载的三窗／有界103方案仅准备，保留原数学／协议／失败源读回，不猜复制API、等待、映射或cache修复。[结果](tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md)／[ADR_25](ADR/ADR_25.md)／[下一方案](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)／[恢复点](tools/pose-v1/evidence/plddr-position-20261010-r1/next-checkpoint.json)。以下已完成成果与当时的下一方案按历史读取。''')
insert_after_title('PROJECT-PROGRESS.md','''## 当前检查点：公开管理器与较高来源位置对照完成

本轮批准范围已完成：合法SDK占位使源实际位于100667392／100697664，动态100对＋VPU100对2388000 FP32逐位正确，227合成编码ID／实际PTS过，公共自有块全部归还。Native／ARM位置12＋字节8拒绝；原主／Host107身份保持。本批规整0，无模型Session／NPU前向，旧坏块未复现、根因仍待。全测试／代理会话结束。[结果](tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md)／[ADR_25](ADR/ADR_25.md)／[恢复点](tools/pose-v1/evidence/plddr-position-20261010-r1/next-checkpoint.json)。

首版全流程已贯通，当前处于并发数值可靠性定位，管理粗估83/100不变，不是测试通过率。下一[真实混合Engine无视频有限对照](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)仅准备，未新模型门检。稳定103、持续5Hz／长期、HDMI／采集终版／零拷贝仍待。以下“当前”检查点均为历史。''')
insert_after_title('DIFFICULTIES.md','''2026-10-10当前：[ADR_25](ADR/ADR_25.md)记录公开容量／合法较高位置对照：DefaultMemManager公开地址空间确认，96MiB SDK自有占位未触碰数据，实际两源100667392／100697664动态100及VPU100全正确、公共块全部归还。本批规整0、根因未修；约96MiB位置不能替代实际模型104MiB／NPU生产。下一原Engine无视频有限对照仅准备。[结果](tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md)／[方案](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)。以下当前为历史。''')
insert_after_title('REFERENCES.md','''2026-10-10当前：[公开管理器与源位置结果](tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md)／[ADR_25](ADR/ADR_25.md)／[公开审计](tools/pose-v1/evidence/plddr-position-20261010-r1/manager.acceptance.json)／[完成证据](tools/pose-v1/evidence/plddr-position-20261010-r1/completion-review.json)／[恢复点](tools/pose-v1/evidence/plddr-position-20261010-r1/next-checkpoint.json)／[下一无视频真实引擎对照](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)。两独立100对、227图像过，不是模型根因修复。以下当前为历史。''')
insert_after_title('ToDoLists.md','''2026-10-10当前：公开PL DDR管理器／容量与合法较高SDK来源对照完成，动态100对＋VPU100对2388000 FP32正确／227图像PTS过、自有块归还、规整0，全项目程序与代理会话结束。无模型／NPU前向，旧192异常仍未解决。下一[原混合Engine移除视频负载三窗→103](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)仅准备，尚未执行。先读[恢复点](tools/pose-v1/evidence/plddr-position-20261010-r1/next-checkpoint.json)。稳定并发103／持续5Hz／长期／HDMI／采集终版／零拷贝待，以下待办为历史。''')
insert_after_title('ADR/README.md','''2026-10-10当前：[ADR_25](ADR_25.md)独立记录公开分配器与合法较高源位置：96MiB SDK占位不访问数据，动态100／VPU100对正确、自有块归还，模型根因仍未修。原数学／模型／SDK／BOOT保持，规整0；[结果](../tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md)／[下一原Engine无视频有限对照](../tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)仅准备。以下当前为历史。''')
print('Position completion archived in project roots and ADR25.')
