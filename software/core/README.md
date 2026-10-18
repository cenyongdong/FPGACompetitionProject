# 正式运行核心

2026-10-17新增可复用HDMI模块：`display/hdmi_canvas.*`负责SDK无关的RGB24→RGB565格式适配，`display/hdmi_output.*`在SDK主线程持有双UDMA帧并管理采纳／STOP／释放。独立构建与实屏结果见[HDMI应用](../hdmi_demo/README.md)。旧演示链接与推理核心未切换；共享Engine的设备hook仅在隔离导出副本中，模型实时联动因SDK上传失败尚未通过。以下描述仍对应旧演示实际链接。

这里是当前演示主链唯一使用的核心源码。`software/pose_v1`及历史工具保留原路径和原内容，供旧验证包追溯；维护当前演示时从本目录进入。原始来源、构建别名及前后哈希见[迁移清单](../../tools/pose-v1/evidence/core-refactor-20261013-r1/source-migration.json)。

后续接入请查[接口与开发指南](INTERFACES.md)：包括每个功能模块的接口、线程归属、资源所有权、异常传播，以及保留历史声明与当前实际链接实现的区别。

## 阅读顺序与职责

| 顺序 | 模块及入口 | 输入、输出与所有权 |
|---|---|---|
| 1 | `input/csi_io.py`、`tcp_receiver.*` | MAT原始complex128→PIWCSI1完整记录→拥有值Window；TCP边界不当作记录边界，单槽仅替换尚未消费的窗口 |
| 2 | `input/preprocess.*` | 固定`[3,3,30,20]`复数→FP32`[1,180,60]`；幅度、unwrap、线性校正、复指数重建的运算顺序保持 |
| 3 | `inference/application_core.*` | 主线程串行持有唯一Engine，Session输出100分数与100×14×3姿态；异常后永久停止，不重试或重建 |
| 4 | `inference/read_input_bridge.cpp`、`host_cpu_adapter.*` | 公开SDK将设备输入搬入独立Host暂存，调用原common数学核，再写回原输出；不直接解引用ADDR/BOTH |
| 5 | `diagnostics/` | 保存首次原始Host字节、拥有快照、计数及存储身份；异常后两轮公开源read只读取证，诊断错误不掩原错 |
| 6 | `display/display_process.*`、`display_worker.cpp` | 一次IPC信用传递拥有值；子进程只处理骨架和像素，不能继承SDK、VPU、UDMA或寄存器描述符 |
| 7 | `video/timed_resident_encoder.cpp` | 拥有NV12→两缓冲V4L2队列→拥有压缩packet；QBUF归驱动，DQBUF归应用，QUERYBUF cookie保留 |
| 8 | `stream/h264_access_unit.*`、`timed_guarded_rtsp.cpp` | packet→完整拥有AU→live555事件线程；容量8，错误或超限停止参考链，不随意丢P帧 |

应用编排仍在`software/demo/board`：`main.cpp`负责生命周期，`demo_options.*`只解析参数，`demo_engine.*`集中配置诊断，`demo_video.*`分别封装三个工作线程，`demo_results.*`拥有并保存全部实际输入和输出。主机入口在`software/demo/host`。

## 线程、释放与错误

Engine在主线程创建、调用和销毁。接收线程只发布完整拥有值；绘图线程、编码线程、网络线程各自负责自己的资源。显示子进程在设备和线程初始化之前exec，网络事件线程唯一拥有live555对象。

正常结束：停止输入生产→绘图线程结束→VPU drain/LAST→关闭AU通道→网络对象回收→工作线程join→结果及诊断保存→销毁Engine。异常路径保持原错误，执行abort STREAMOFF、唤醒等待者和子进程回收，不能复用失败Engine。

CPU异常先保存首次Host坏值与post-copy拥有快照，再执行有界两轮源读取；晚值不能修补旧值。ready、layerCount和Linux缓存操作不是硬件写完成的证明。旧DATA坏读根因尚未解决，本轮不恢复该排查。

## 构建与接口

头文件与实现文件按功能同放，函数、类型、命名空间及协议均沿用批准基线。构建仍由`software/demo/baseline-lock.json`逐项核对，并将源码导出到新构建目录的`baseline`；相同目标不能混编旧核心。导出别名也是头文件include名，文件名在核心内唯一。

保持GNU++17、`-O2 -DNDEBUG`、`-ffp-contract=off`、SDK3.39.0、固定JSON/RAW、原CPU/Gather注册、Matmul NPU分配、`reset(1)`和最终745阈值。注释与目录调整不构成新算法或新同步语义。

`Regression.cmake`仅将原检查器链接到新核心，测试正文不改。`verify_core.py`提供原文件哈希、C++逐token、既有SDK无关检查器及旧实现／原参考的字节对照；`validate_board.py`提供已批准的CPU107→三窗口顺序门检。编译、Host数学、模型输出、视频来源和长期可靠性分别记录，不互相替代。

## 维护规范

- 四空格缩进、同行左花括号，函数和不同逻辑步骤用空行分开；中文注释说明目的、契约和已知限制。
- 共享头文件只表达必要契约；功能通过公开最小接口协作，不包含其他功能的`.cpp`。
- 数值、SDK、锁和计时敏感段保持表达式、操作顺序及变量生命周期；调整后重新核对原参考和身份。
- 更新当前锁时单独保存修订及迁移记录，不能回写旧完成清单中的哈希。旧副本是冻结证据，当前实现只维护本目录。
