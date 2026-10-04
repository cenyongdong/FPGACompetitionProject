# 首版阶段结果（2026-10-04）

## 已完成

- 用户批准PS为主的回放→混合推理→HDMI/RTSP首版；当前只实施独立、不会访问未知硬件的阶段。
- 建立`Logs`、C++预处理模块、原始CSI发送端、协议说明、只读审计、构建和数值检查工具。
- FPAI为运行中的`ubuntu20.04:custom`容器，原挂载`D:\FPGACompetitionProject:/workspace`；
  实际arm64 Icraft/CustomOp 3.39.0，交叉GCC9.4，源码从当前worktree独立复制至临时目录。
- Conda独立验证环境已完成：Python3.10.21、NumPy2.2.5、h5py3.16.0、PyWavelets1.8.0。
  首次在线创建因Python包TLS连接中断失败，随后缓存离线安装成功，未改渠道/证书/既有环境。
- 板端FAT16直接只读解析，9文件与原镜像大小/哈希全部一致；没有挂载或改启动文件。
- 零幅值复数带符号零移植错误已定位、修正，保留首次失败证据。
- 9类输入在Linux主机与实际Lite运行；3份真实CSI及常量/零/随机输出逐位一致，
  真实样本5.70319/5.78065/5.72649ms。四类非法记录均拒绝。
- arm64二进制SHA256 `65d44aa2aff5ffe2975300b27b1325dc7b25d5cb71cd6f85ee5076b4aa4a59b2`；
  可复现构建脚本再次构建得到相同哈希，与板端实测二进制一致。
- Windows TCP回环强制碎片读取，3个原始CSI窗口/帧号字节不变；只是发送端测试，未接入板端。
- 离线替换Windows NumPy angle为Python math.atan2的诊断未解释π边界差异；保留负结果，不修改原算法。

## 阻断与未验收

1. **启动配套未知。** 已知文件一致不等于已知运行位流。uEnv引用p2的download.bit，前次根目录未找到；
   不知道加载是否成功、BOOT内包含哪个AI系统以及当前HDMI映射。等待用户保留的完整启动串口日志，
   不尝试默认AI/HDMI寄存器或更换BOOT/位流。
2. **边界数值未通过。** 0.75rad斜坡误差7.5051e-14；±π合成斜坡分别有6.24063/5.76522最大绝对差。
   相位展开在此边界对微小浮点差异敏感是排查方向，尚未唯一证明因果，不能当作普通小误差忽略。
   未定义/放宽容限或改变算法，总体预处理门检待进一步讨论。
3. **闭环尚未实现。** 未运行ONNX/参考模型/板端混合推理；未实现板端TCP服务、有限队列、
   骨架绘图、HDMI、VPU/live555 RTSP或30分钟测试。NPU和正式双路验收均未通过。
4. 实际训练服务器NumPy/软件栈未在本阶段查询；原方法来源代码哈希和Windows参考依赖版本已记录，
   不能以当前Windows数值对照代替完整训练环境复现。

## 下一步

先读取用户放入`Logs`的启动日志，核对运行位流与SDK配套；再就π边界处理/误差容限提出具体方案并获同意。
启动变更、新依赖、模型修改、新增FPGA工程均遵循审批规则。不得以网络骨架备用方案、全CPU或电脑推理
替代正式首版验收，不自动重启或改板卡配置。

证据：`evidence/board-audit.json`、`boot-source-comparison.json`、`host-preprocess-initial-failure.json`、
`host-preprocess.json`、`board-preprocess.json`、`asset-manifest.json`、`conda-explicit.txt`、`build-reproduction.txt`。
