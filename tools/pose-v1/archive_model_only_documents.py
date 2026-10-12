"""Archive this finished diagnosis, keep earlier failures and next plans historical."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def insert(rel,text):
    p=root/rel;s=p.read_text(encoding='utf-8');assert 'MODEL-ONLY-RESULTS-20261010' not in s
    title,rest=s.split('\n',1);p.write_text(title+'\n\n'+text.strip()+'\n'+rest,encoding='utf-8',newline='\n')
insert('Agents.md','''- 真实混合模型无视频有限对照本批结束（2026-10-10）：model-only-r1 9ed61d9d…d925741／manifest34c3c25c…e355903，403包98来源；原主fbf330d7…cb8702d／Engine／桥／CPU数学／402非清单载荷／SDK／模型／RAW／BOOT逐位保持，Host107／12注册59600及原异常读取身份复用，未新入口Host107。Native／ARM各9拒绝、103调度顺序／窗口与返回值拥有／异常停止／不突发补帧／独立flush过。三窗4正确60400＋103正确1555300合107前向1615700 FP32逐位旧参考，CSI／输入／完整100分数姿态保存后比较；六Host＋输入0／七ZG回调、1173融合、0→745过。192真实源109232128／109285376同旧失败，1712对象／856shadow身份合法稳定、963copy元数据／856查询全234，107次582首次638/poll1；Host目标mod64覆盖0/16/32/48均FP32对齐正确，不作64对齐修复。主线程Engine生命周期／七项flush／exit0／stderr空／所有阶段原内核同；无VPU／绘图显示／网络／HDMI、正常新设备读0、异常设备源读触发0，本批规整0，无清缓存／重启／CMA／BOOT变化。最终MemAvailable700208KiB/CmaFree9312／普通单位1仅现场，所有项目程序／端口／代理会话关闭。旧坏块未复现、根因未修，移除视频同时改变启动／堆／保存时序，不认定VPU有责或稳定并发103／5Hz／长期。ADR_26、MODEL-ONLY-RESULTS/NEXT及model-only-20261010-r1 completion/next-checkpoint为当前入口；下一同身份模型／合成VPU单因素对照仅准备未实施，原异常／两晚源继续保持，不猜cache／等待／私有映射／零拷贝。管理粗估83/100保持，旧当前为历史。''')
insert('Done.md','''## 2026-10-10：真实混合模型无视频三窗及103窗口完成

### 工程内容总结

新独立model-only-r1 9ed61d9d…d925741／manifest34c3c25c…e355903，403包98来源。原Engine／桥／数学／主ELF／载荷／SDK／模型／RAW／BOOT保持，Host107／12注册59600明确身份复用。SDK-free调度与异常停止Native／ARM各9拒绝、103样本顺序／拥有值／独立flush通过。三窗4次60400 FP32及103次1555300 FP32合107前向1615700 FP32逐位旧参考，完整CSI和模型输入／100分数／100姿态保存；六计算Host／输入0／七ZG组、1173融合与0→745核验通过。

实际192源109232128／109285376同旧失败；1712对象行／856shadow稳定，856查询全234、107次582首次638/poll1，无额外等待。Host目标mod64为0／16／32／48均正确，不能据此推广64对齐修复。无VPU／显示／网络，本批规整0；七项flush成功、exit0／stderr空／内核原字节同，所有项目程序和代理会话结束。资源最终700208KiB可用／CmaFree9312／普通单位1，仅现场。

### 对后续开发的参考

这次是实际NPU生产的无视频完整103通过，旧坏块未复现、根因未修；保存I/O、启动和堆条件不同，不能认定VPU有责或并发／长期通过。原失败和两晚源保持。下一同一新二进制的模型／合成VPU对照仅准备，不带显示／TCP／RTSP，先独立生命周期门检。管理粗估83/100保持。[结果](tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md)／[ADR_26](ADR/ADR_26.md)／[下一方案](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)／[恢复点](tools/pose-v1/evidence/model-only-20261010-r1/next-checkpoint.json)。以下成果与当时后续方案为历史。''')
insert('PROJECT-PROGRESS.md','''## 当前：真实混合模型无视频三窗／103诊断完成

107实际前向1615700 FP32逐位旧参考，真实192源与旧失败相同、1712对象／856计数合法，数据保存完整；Native／ARM契约与原Host身份通过。无视频／显示／网络，规整0、内核同、程序及代理连接结束。旧坏块未复现，根因仍未解决，不能以无视频通过认定VPU有责。[结果](tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md)／[ADR_26](ADR/ADR_26.md)／[恢复点](tools/pose-v1/evidence/model-only-20261010-r1/next-checkpoint.json)。

项目仍处首版全流程贯通后的并发数值可靠性定位，管理粗估83/100不变。下一[同身份模型／合成VPU对照](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)仅准备，稳定并发103／长期5Hz／HDMI／采集终版／零拷贝仍待。以下当前为历史。''')
insert('DIFFICULTIES.md','''2026-10-10当前：[ADR_26](ADR/ADR_26.md)记录无视频真实混合模型4＋103全部完整输出正确、192源同旧失败／对象和计数稳定。坏块未复现，视频不是已证根因；堆、初始化与保存I/O差别保留。规整0、全项目程序／会话结束。下一同身份仅模型／合成VPU对照仅准备。[结果](tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md)／[方案](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)。以下当前为历史。''')
insert('REFERENCES.md','''2026-10-10当前：[无视频真实模型结果](tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md)／[ADR_26](ADR/ADR_26.md)／[完成证据](tools/pose-v1/evidence/model-only-20261010-r1/completion-review.json)／[恢复点](tools/pose-v1/evidence/model-only-20261010-r1/next-checkpoint.json)／[下一同身份VPU单因素方案](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)。107完整前向正确，旧根因未修，以下当前为历史。''')
insert('ToDoLists.md','''2026-10-10当前：无视频真实混合模型三窗＋103完成，107前向1615700 FP32逐位正确、对象及计数合法，规整0、全会话结束。旧数值故障未复现／根因未修，下一[同身份模型／合成VPU有限对照](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)仅准备，未新视频或并发门检。先读[恢复点](tools/pose-v1/evidence/model-only-20261010-r1/next-checkpoint.json)。稳定并发103、长期／持续5Hz、HDMI／采集终版／零拷贝待。以下当前为历史。''')
insert('ADR/README.md','''2026-10-10当前：[ADR_26](ADR_26.md)独立记录实际混合模型移除视频负载的三窗／103通过，源地址同旧失败但坏块未复现、根因未修；无VPU／显示／网络、规整0。下一同身份模型／合成VPU单因素设计仅准备。[结果](../tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md)／[方案](../tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)。以下当前为历史。''')
print('Model-only completion archived; old failures kept.')
