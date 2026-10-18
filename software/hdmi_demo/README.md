# HDMI独立接入应用

用户最新明确要求暂停，等待唤醒。本轮已在原BOOT回退核验、失败取证和本地静态审查结束处停止，无后台续作；未启动更多候选构建、部署或板测。恢复须由用户明确唤醒；旧DATA继续独立暂停。

2026-10-17观测v2补充：`build_hdmi_shared.py monitor-v2`已交叉编译并完成固定来源／SDK／模型核验；导出Engine增加apply前公开Device ABI回调和apply原异常保存后的同Device快照回调，诊断失败不替换原错误。该包尚未执行三窗推理，因为独立DMA门禁在4KiB写失败，HDMI START未执行；不能把编译成功或独立探针快照成功记作Engine异常分支验证。当前已按批准包回退原BOOT。[r2证据](../../tools/pose-v1/evidence/hdmi-live-20261017-r2/REPORT.md)。

2026-10-17：动态DDR帧、翻帧、历史真实骨架及在途STOP／释放通过，用户确认画面成功。实时新模型闭环尚未通过，SDK在Session.apply上传参数时异常；不得把回放记为新推理。[完整报告](../../tools/pose-v1/evidence/hdmi-display-20261017-r1/REPORT.md)。

PS使用原`skeleton_render`做候选选择、投影、骨架和文字绘制，`hdmi_canvas`仅做1280×720 RGB24→1920×1080 RGB565LE双线性转换。PL完成DDR读帧、FIFO、扫描和HDMI，不调用VPU／RTSP。原数学、CPU注册、模型和SDK不改。

`main.cpp`是有界三窗联动入口：导出的共享Engine在Session.apply及绑定验证后通过显式`Config::on_device_ready(Device const&)`交付同一设备，由主线程建立HDMI输出，避免两个独立分配器。每份实际输出先完整保存再按ADR_48门检，然后显示约5秒；显示先停止释放再销毁Engine。该hook仅存在于构建脚本生成的隔离副本，不改正式核心或旧演示。当前失败发生在hook之前。

`FPGA/hdmi_candidate/software/saved_skeleton.cpp`是已验收真实结果回放入口，无Session／新NPU推理或PL DDR参数上传。三个历史来源固定S11_01_308/309/310，原ID1000000/1/2，各8秒；重复扫描不计新姿态。程序结束正常STOP后黑屏。

构建位置Windows D:/FPGACompetitionProject，交叉编译容器FPAI，ARM64 GCC9.4／CMake3.24.2，六份SDK身份须匹配证据；每步有界、失败保留、编译容器最终停止。`build_hdmi_display.py <新revision>`构建frame_probe，revision以`saved-`开头则构建saved_skeleton；`build_hdmi_shared.py <新revision>`构建三窗共享联动。脚本在证据树和.local创建新目录，拒绝覆盖；源码快照、依赖、ARM产物及每步退出码均保存。共享构建依赖已核验的`.local/shared-resident-source-20261015-r1`及共享模型交付包，完整复制来源也在本轮build-shared-r2/source和package中；当前目录CMake是导出构建模板，不能直接以此目录配置代替导出。

板端执行位置/root/hdmi-display-20261017-r1，实际参数与完整控制脚本见证据中的memory-code.py、repeat-code.py、shared-r3-code.py、saved-code.py。frame_probe参数`--memory`仅内存对照，`--patterns`两图案，`--user-requested-repeat`严格限定该次已归档错误和停止tag的清错重测，不是通用自动恢复。saved_skeleton参数为已核验回放包目录、新输出目录；pose_hdmi_demo参数为共享包、新输出目录、`--allow-device-init`。本页提供复现依据，不授权重跑故障负载。

Output只采用公开SDK分配、写入和寄存器接口；两帧共8,294,400字节，实际地址运行时分配、64字节对齐并核对池范围。show的采纳预算200ms、close预算500ms；不能以ready或缓存操作代替STOP。首次reader fault2仍待定位；新模型SDK异常必须停止，不从本页推导复位、重启、BOOT替换或放宽时序／数值门禁。旧DATA持续暂停。
