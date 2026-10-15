# 稳定性验证r1：观测接口兼容失败，现场保留

日期：2026-10-15。用户批准先验证新包，再做30分钟连续满速／最多90000次推理，不叠加视频或网络。**r1首次验证由观测器错误中止，没有产生完整推理输出；不将此结果写成模型崩溃、内存泄漏或数值失败。**

原编译包SHA256为`4c01c92cca92e5d76f427e121fa5c770f61dff3de49a26a75bf3d3fe20351070`，模型／RAW为ADR_48固定共享图。独立常驻入口复用原推理核心和score>0.2／3mm门检；只为独立诊断副本增加前三帧常规元数据采样界限，不改变数学、CPU注册、NPU分配或CPU异常原Host字节／两轮源读取路径。源码清单见[resident-source-manifest.json](resident-source-manifest.json)。

板端目录`/tmp/wifi-pose-shared-stability-20261015-r1`。观测器读取`/proc/78302/task/78302/children`失败，控制器停止子进程，退出1、完整推理帧0。只读兼容探测随后确认板端内核对自身进程同样没有该可选接口，RSS／PSS所需的status／smaps_rollup存在。控制器的`killed_child=true`、`graceful_engine_cleanup_verified=false`保持原记录，不将强制停止写成优雅销毁。

完整返回：[basic.tar.xz](basic.tar.xz)、[controller-summary.json](returned-basic/run-basic/controller-summary.json)、[monitor-failure.json](returned-basic/run-basic/monitor-failure.json)、前后内核／资源／身份及回传清单。SDK／BOOT未改，内核日志无新增；后续只读进程检查无本批推理进程，FPGA operating。初始沙箱MSYS管道错误发生在SSH客户端启动前，保留01-state原日志，获工具审批后只读核验正常。

按AGENTS失败停止约束，没有自动重跑。代理先完成新r2观测器修复和4项本机兼容检查，用户明确回复“允许按原预算继续”，才在r2新目录／新Session继续；两个ARM二进制和推理核心未因此改变。r2曾因本地传输脚本误指旧助手而被路径保护拒绝上传，确认r2目录仍空后修正助手再完成首次部署，没有覆盖旧包或重新运行该失败Session。最新实际结果见[r2报告](../shared-stability-20261015-r2/REPORT.md)。

本次第一次中止不支持任何内存稳定性结论；30分钟压力阶段未在r1启动。原包、原脚本、失败日志和完整清单保持，修复另存r2。
