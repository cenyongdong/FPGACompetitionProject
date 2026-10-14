# Engine计时诊断开发交付证据

日期：2026-10-13。范围为源码开发、静态身份核验、离线合成测试、既有FPAI交叉编译及本机打包；没有SSH、模型前向、NPU Device/Session、VPU/TCP、规整、重启或部署。旧DATA故障定位继续暂停。

## 实际验证

- `offline-r3/analysis-tests.stderr.txt`：13项Python测试通过，覆盖区间并集/嵌套扣除、回调重叠/缺失、错误范围、非法CPU时间、逻辑复制字节、输出失配、失败批、SDK原始单位、证据改值与报告覆盖拒绝。
- `offline-r3/checks.json`和`result.json`：Windows既有g++编译SDK无关计时器，`basic/thread/capacity`三种合同通过。Windows线程CPU/rusage不可用，字段为null。
- `linux-native/build-steps.json`及完整stdout/stderr：FPAI主机g++运行相同三个SDK无关合同；线程CPU/rusage有效、异常标记、错误线程和有界容量通过。不链接SDK，不打开Device/Session。
- `linux-native/result.json`：合成sleep跨度墙钟2.081676ms、线程CPU0.023900ms、自愿切换1、缺页0；这是Linux计时合同示例，**不是Lite或模型耗时**。
- `D:/FPGACompetitionProject/.local/pose-v1-build/engine-timing-20261013-r3/build-result.json`：最终ARM64交叉编译成功，29个独立Docker步骤exit0；ARM/public SDK头与所读Windows版本匹配，实际六个库身份保存。既有私有助手unused警告来自未修改的host_cpu_adapter.cpp。
- 最终导出：`.local/engine-timing-source-20261013-r2`；交付包：`.local/engine-timing-delivery-20261013-r2`。模型及旧三窗口CSI/完整输出经实际哈希核验，包仅准备，未上传。
- `delivery-review.json`：正式锁定源码不变、新源码/编译/包/二进制/测试身份闭合；全部“不曾板测”的边界单列。

## 已保留失败及修订

- 首次Python临时目录写入拒绝；随后工作区内`mkdtemp`的限制模式也拒绝写入，完整第二次日志保留在`offline/analysis-tests.stderr.txt`，不重写为通过。改为工作区UUID目录，使用默认权限并保留合成夹具；`offline-r2`通过12项，新增哈希改值合同后的`offline-r3`通过13项。
- 首次Docker API命名管道在沙箱中被拒绝，失败构建保留`.local/pose-v1-build/engine-timing-20261013-r1`完整step0日志。通过执行工具对既有Docker访问的审批后，在新r2/r3构建目录完成；没有安装或启动新的容器、没有板端操作。
- r1导出/交付和r2编译是分析器增加哈希核验之前的版本，保留原身份。最终r2导出/r3编译的C++输入与前一构建相同，二进制SHA256一致；Python分析器版本分别绑定原各清单，不覆盖旧产物。

## 测量能力边界

本次证明采样/分析合同及公开接口可编译，不证明当前模型的各项实际耗时。SDK tuple单位/累计语义、硬件层序映射待新的有限门检；getLayerTime的ms说明不能推出纯算术时间。DDR-stall、纯NPU算术、精确SDK调度和OS runqueue时长没有独立计数，明确输出null。桥逻辑字节不当作DDR总通信量，多个观测层次不得重复相加。

入口：[程序说明](../../../../software/engine_timing/README.md)。本批没有运行三种板端模式；后续范围和负载以用户明确任务为准，不能把这份交付变成自动续跑许可。
