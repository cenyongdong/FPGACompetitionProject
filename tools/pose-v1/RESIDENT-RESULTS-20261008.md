# 同进程有限常驻工作者结果（2026-10-08）

**启动最小修正三次回归、主线程Engine＋后台VPU的三帧与27窗口有限运行已通过。** 常驻指测试窗口内保持一个编码器上下文，不是已安装的永久服务，也不是在线RTSP/整机5Hz或长期验收。

## 实现与身份

编码线程独占VPU，主线程独占Engine，所有SDK数学/注册/模型/RAW/BOOT、profiling-off及reset(1)/0→745保持。采用两端实际协商2缓冲、prime2与opaque cookie；保存owned NV12/packet，输入先复制再QBUF、capture先复制后归还。队列容量2，满覆盖最旧未消费帧；采样popLatest合并旧帧单独计数，重复最新画面不算新推理。

PTS来自源选择后的steady_clock实际采样时间，错过时隙不补发突发帧。初始NoInput显式标记；首capture5秒、Engine60秒、就绪后20秒、总180秒/最多1000编码帧。Host外部420秒有实测预算依据，原300秒超时保留。大尺寸数据只保存不同来源与首帧重复，完整码流/逐帧源/时间/FNV1a64检查码保存；原始证据清单与传输使用SHA256。

程序`f4f15b7ea8806549ad91ca4e3bd69f0fcc5ea580722b18802d5268730efe7060`，包manifest`271be561c4baad831b5c44465ed13f73fbf69f831290b0c5d3ee936d3bc56575`，402载荷/23构建来源、15SDK头/两后端库匹配。GCC9.4/CMake3.24.2/Icraft与CustomOp3.39.0，无新依赖。原三条编译warning保持，无新增warning。

## 门检结果

| 阶段 | 结果 |
| --- | --- |
| 启动 | 独立两缓冲候选三次进程启动、24完整前向/30编码全部通过，无规整/重启；[证据](VPU-STARTUP-RESULTS-20261008.md) |
| Host | 107例/12注册/22输出59,600 FP32逐位原参考；容量2/覆盖/最新选择/不可变复制/停止/异常传播测试通过 |
| 三帧＋重复 | 四次前向全部输入/分数/姿态逐位原板端，493完整解码帧，四来源都出现，重复首帧NV12一致 |
| 27窗口＋重复 | 28次2Hz固定窗口回放逐位原板端，494完整解码帧，28次来源全部出现，重复首帧NV12一致 |
| 队列 | 两阶段均published=consumed，overwritten/coalesced=0，high_water=1，容量上限2 |
| 时钟与所有权 | 987个实际采样PTS递增、源生成时间不晚于采样，完整IDs/源/关节核验；上下文不重开、正常LAST/全部归还/STREAMOFF |
| 系统 | 两硬件阶段exit0/stderr空、各自内核前后同、BOOT/SDK保持，FPGA最终operating；测试与会话全部关闭 |

三阶段成功回传397个哈希文件；32次完整结果包含483,200个有限FP32输入/输出值。987视频帧中只有32次新推理，其余为初始化NoInput或显式重复；5530次关节可见性检查通过。完整时间与重复计数见[完成核验](evidence/resident-20261008-r6/completion-review.json)。核心旧5.25Hz与本轮2Hz输入不代替整机吞吐。

## 失败与修正边界

r5后台Engine所有者首次输出读取被原有限性门禁拒绝；七ZG/七Host、745及ready齐全，内核不变，未发布模型画面、未进入27阶段。失败108文件完整保存，清理成功，未降低检查或复位。

r6仅把Engine创建/前向/保存/销毁放回此前通过程序使用的主线程，编码仍后台，硬件活动/数学/CMA/同步政策保持；三/27全部通过。该对照支持首版采用已验证主线程调用模式，**不证明SDK普遍禁止后台线程或其内部根因**。厂商Actor参考存在工作线程前向，具体构建/调用模式不同，不以当前结果作通用限制。

原r1/r3/r4本机构建原型、r2Host、r5失败、r7分配取证和r8Host超时均保留；[ADR_02](../../ADR/ADR_02.md)记录两缓冲与所有者模式的实际方法、取舍和限制。

## 主机审查与后续

[活动段预览](evidence/resident-20261008-r6/preview/active-review.mp4) · [完整预览](evidence/resident-20261008-r6/preview/review.mp4) · [27来源联系图](evidence/resident-20261008-r6/twentyseven-video-review/contact-sheet.png) · [恢复点](evidence/resident-20261008-r6/next-checkpoint.json)

预览按名义10fps建立离线时间轴，活动段裁去29.7秒初始化并用现有libx264重编码197帧，属便于审查的派生物；原H264和真实PTS/源轨迹未改，验收解码使用原H264。不得用预览帧率宣称姿态10Hz、物理精度或真实端到端延迟。

下一按已批准F0路线核对实际AU分界/live555线程通知，再接入owned AU在线RTSP。阶段异常停止，不自动重试/规整；CMA仍256MiB，原六缓冲源保持。未知输入、长时间启动、线上网络争用、显式色彩、HDMI1080p60时序/安全scanout和整机5Hz/30分钟仍待。

## 后续复现入口

当前采用`prepare_resident_owner_package.py --output 新目录`与`Build-Resident.ps1 -Package 新目录 -BuildTag 新标签`，绑定已验证主线程源到构建文件resident_check.cpp。`prepare_resident_package.py`保留为后台所有者实验来源，不作为当前默认入口。旧r6包/构建不重写；新程序必须重新核对身份和门禁，不复用旧SHA或验收改名。

Lite新工作目录放置包、程序、build-result、同身份build门禁及外部`run-resident-stage.sh`。先host-check（420秒）、完整回传经resident_gate核验，再resident-three与resident-27（各180秒）。Host/数值/视频门禁逐阶段；review_resident_video使用已有OpenCV，原始码流用于验收，派生预览单独标记。以上是新版本复现入口，不要求重复已完成的本轮测试。
