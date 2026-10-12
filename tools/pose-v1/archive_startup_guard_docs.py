"""Archive reviewed current outcomes, retaining earlier checks as history."""
from pathlib import Path
import json
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/startup-guard-20261009-r1';c=g.load(e/'completion-review.json')
assert c['starts_executed']==2 and not c['start3_executed'] and c['failed_pose_changed_FP32']==652
def prepend(rel,body):
    p=root/rel;t=p.read_text(encoding='utf-8');assert body not in t;head,rest=t.split('\n',1);p.write_text(head+'\n\n'+body.strip()+'\n\n'+rest.lstrip('\n'),encoding='utf-8',newline='\n')
result='[结果](tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md)／[ADR_20](ADR/ADR_20.md)／[接入契约](tools/pose-v1/INVOCATION-EVIDENCE-INTEGRATION-NEXT-20261009.md)／[恢复点](tools/pose-v1/evidence/startup-guard-20261009-r1/next-checkpoint.json)'
prepend('Done.md',f'''## 2026-10-09：独立启动第1轮通过，第2轮有限姿态失配，保存模块验证

### 工程内容总结

沿冻结stage-guard-r1，不重建主程序或重复Host107，预定三次103独立启动。第1次103/1555300FP32、593编码563网络全内容通过，4.999251559Hz严格5Hz未过。第2次返回38，前37正确558700FP32；S21_19_319/inv37输入及100分数正确、姿态652值不同/最大0.5078125且有限。最高分及其42坐标不变，35其它候选不能按简单整行交换解释；第3次停止未执行。合140正确完整前向2114000FP32，完整异常原CSI/输入/分数/姿态保留。

收到39/消费返回38/覆盖0，发送40非ACK。失败385捕获355网络/35来源966关节仅前缀，inv35/36未捕获、4采样尾未出，不称完整视频或正常LAST。第二轮自主规整一次14.59069ms，实际普通512KiB单位0→4，仅资源措施；未清缓存/重启/改CMA/BOOT/SDK。内核同、两abort STREAMOFF0/子回收/source0/Engine join后销毁/端口与连接释放。

### 对后续开发的参考

保存函数再次比较失败，跳过后续元数据/ARM参考；presaved38套/inference37行/timing38行，不回填638初值。CPU未拒绝，旧两轮源读取未触发，原shadow生命周期不足以覆盖有限输出异常。SDK-free单帧拥有值/独立flush模块Native/ARM各12拒绝及原异常/后续任务保存通过，尚未集成，不称数值修复。匹配SDK审计区分Linux缓存助手、UDMA同步和PL DDR ADDR，六Host生产组223/234/477/481/638/720无当前等待循环；当前只新查582的638，不涵盖649等读取。{result}。''')
prepend('PROJECT-PROGRESS.md',f'''## 当前检查点：2026-10-09 独立回归有限输出异常，先补齐取证

预定三轮：第一轮103全内容通过、严格速率4.999251559Hz未过；第二轮第38次姿态652值失配，最佳骨架没变仍停止，第三轮未执行。合140正确完整前向2114000FP32，完整异常保留；元数据/ARM参考被重复保存门检跳过。新SDK-free单帧拥有值/独立flush已Native/ARM验证但未集成，根因未解。规整一次0→4高阶单位、14.59069ms，仅资源策略；全部代理测试和连接关闭。管理粗估83/100保持，稳定5Hz、长期、HDMI、采集终版及合法零拷贝继续待。{result}。''')
p=root/'PROJECT-PROGRESS.md';t=p.read_text(encoding='utf-8').replace('## 当前检查点：2026-10-09 新快照/582完成检查及103完整回归','## 历史检查点：2026-10-09 新快照/582完成检查及103完整回归',1);p.write_text(t,encoding='utf-8',newline='\n')
prepend('DIFFICULTIES.md',f'''2026-10-09最新：[ADR_20](ADR/ADR_20.md)记录有限姿态652值/35候选失配、最高分骨架不变以及保存再比较导致元数据缺失。新SDK-free单帧拥有值/独立flush模块测试通过，主程序接入待；原异常/拒绝及源码保持。静态638仅覆盖582，649结束720；[SDK审计](tools/pose-v1/SDK-MAPPING-AUDIT-20261009.md)区分UDMA同步与PL DDR映射，不猜零拷贝修复。以下“最新”为历史。''')
prepend('REFERENCES.md',f'''2026-10-09最新：{result}；[SDK搬运/映射审计](tools/pose-v1/SDK-MAPPING-AUDIT-20261009.md)。第一轮通过、第二轮有限姿态失配、第三轮停止；异常完整结果保留，元数据缺口明确记录，独立模块已验证未集成。以下状态作为历史。''')
prepend('ToDoLists.md',f'''## 当前接续：有限输出取证与独立落盘

- [x] 同身份独立第一轮103完整内容/593编码563网络核验，严格4.999251559Hz未过如实记录。
- [x] 第二轮38返回/37正确、39接收及完整异常数据/部分视频；第三轮停止。
- [x] 姿态652值/35行不同，分数及最佳骨架一致；同CSI早前inv10正确，不降为最高分门检。
- [x] 保存再比较耦合定位；SDK-free Frame/flush Native/ARM各12拒绝，原异常和后续任务保存通过。
- [x] 匹配SDK缓存助手、UDMA路径和六Host生产组静态审计，不直接映射或改SDK。
- [ ] 新隔离接入observer/独立落盘，Host107＋实际Host最终比较异常模拟，前门通过后新三窗和单次103取证。
- [ ] 同板异常根因、稳定5Hz/长期、HDMI/采集终版、合法映射与一致性继续待。

{result}。旧阶段通过和失败仍为历史。''')
prepend('ADR/README.md','''2026-10-09最新[ADR_20](ADR_20.md)：独立第2轮有限姿态失配与保存再比较耦合；完整异常保留、第三轮停止。SDK-free Frame/独立flush Native/ARM验证通过，尚未集成，根因及638之外的读取边界继续待。[当前结果](../tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md)。''')
p=root/'ADR/README.md';t=p.read_text(encoding='utf-8');needle='| 20 | [ADR_19](ADR_19.md) | Host复制快照/元数据与582完成检查；新103完整通过，未观察到额外等待 |';assert needle in t;t=t.replace(needle,needle+'\n| 21 | [ADR_20](ADR_20.md) | 有限姿态失配与证据保存耦合；Frame/独立flush测试通过，集成待 |');p.write_text(t,encoding='utf-8',newline='\n')
for rel in ('ADR/ADR_19.md','ADR/ADR_17.md'):
    p=root/rel;t=p.read_text(encoding='utf-8');t+='\n## 独立启动接续结果（2026-10-09）\n\n冻结身份第一轮103通过，第二轮第38次出现有限姿态失配（652值、35候选，输入/分数/最佳骨架一致），第三轮停止。原数据已保存，后续快照元数据被保存再比较抛错跳过。新Frame/独立flush模块已Native/ARM验证但未接入，数值根因仍待。独立新决策和证据见[ADR_20](ADR_20.md)及[当前报告](../tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md)，旧一批通过不改写。\n';p.write_text(t,encoding='utf-8',newline='\n')
prepend('Agents.md','''- 独立启动与有限输出保存接续结束（2026-10-09）：冻结27b9ff09…2769e086/de32738d…96ed48d，未重建主程序/重复Host107。预定三轮103，第1轮1555300FP32/593编码563网络103来源4130关节全过、4.999251559Hz严格未过；第2轮38返回/37正确558700FP32，第38 S21_19_319/inv37/frame100037输入/分数逐位同早前inv10，姿态652值/35候选不同、最大0.5078125且有限，best0及42坐标相同，不能按简单候选整行交换通过。第三轮停止未执行，合140正确2114000FP32。实际39接收/38消费返回/0覆盖，40send非ACK；完整bad结果保存但presaved38/inference37/timing38，measurement.save再次比较抛错跳过同try后面的新元数据/ARM参考，不回填638初值。旧CPU异常捕获未触发；新SDK-free invocation_evidence Frame/独立flush Native/ARM各12拒绝/16字节释放后保持/原异常与后续任务保存通过，尚未集成，失败后无新NPU/VPU/第三次模型测试。自主规整一次14.59069ms，预决策2普通块、实际写前0→4单位，仅资源策略；无清缓存/重启/CMA/BOOT/SDK/数学变化。失败385图像355网络35来源966关节只前缀，inv35/36没捕获、4尾未出，非完整视频/正常LAST。内核同/两abort STREAMOFF0/子回收/source0/Engine join后销毁/端口和全部代理会话关闭，最终MemAvailable747384KiB/CmaFree16492仅现场。匹配SDK审计CacheSyncHost Linux memcpy、UDMA同步属性、当前PL DDR仍ADDR；静态六Host结束223/234/477/481/638/720无当前等待循环，只582新查638，不证明其他读取或DMA fence。ADR_20/17/19、STARTUP-GUARD-RESULTS、SDK-MAPPING-AUDIT及startup-guard-20261009-r1 completion/next-checkpoint为最新入口；下一隔离observer从原拥有shadow保留一帧并独立落盘，Host107＋实际Host有限输出异常模拟后再新三窗/有界103。不重跑start2/start3，不降低完整候选门禁或猜映射/ready/cache；长期/HDMI/零拷贝待。''')
print('Done, current progress, ADR index and recovery instructions archived')
