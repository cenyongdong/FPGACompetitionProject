# 已保存真实板端结果的TCP与PC 3D回放

2026-10-18，Windows `D:/FPGACompetitionProject`。本轮按用户明确批准的C++17＋TCP＋Node.js＋WebSocket＋Three.js路线实施，全部操作位于PC。源码入口：[PC观察台](../../../../software/pc_viewer/README.md)、[骨架发送契约](../../../../software/pose_output/README.md)。

## 实际完成

- 复用S11_01_308/309/310三份已保存且符合ADR_48 v2的真实共享FP16板端输出；逐字节核对与已验收HDMI历史回放包的完整分数/姿态相同。沿用原始帧1000000/1/2及原候选选择，完整原值不改写。
- 原生g++16.2.0编译SDK无关C++发送器通过。每条256字节，经真实回环TCP进入Node后核对，再经WebSocket交付浏览器；三条共768字节，接收与来源SHA256均为 `2598dcb814202c4638a75cdb7093c887b56db2ca58a78fc40d4705c33f024320`。
- 8组必要检查通过：原拓扑、原值/FP32字节、分包/合包、u64大身份、非法记录/顺序/会话、实际C++普通与单字节发送、大身份及拒绝连接、C++截断/NaN文件拒绝。实际WebSocket三记录重编码与TCP来源逐字节相同，7项本机页面/模块资源均HTTP200。
- 内置浏览器实际WebGL2渲染通过；检查逐帧、播放/暂停/结束、速度、视角切换、复位、关节编号和原值详情。详情页14×3共42个文字坐标与接收值按同一7位小数格式逐项一致。画面曾观察到60FPS，仅为本机当前场景采样，不是模型吞吐保证。

## 范围与保留

新模块仅维护 `software/pose_output` 与 `software/pc_viewer`，不改HDMI源码/RTL/约束/构建、既有核心、模型、SDK、BOOT、CSI和显示IPC。未连接Lite，无SDK初始化、DMA、新推理、HDMI START或板测；D45及另一施工线程进度由其原入口维护。

当前只有三个真实姿态，默认2Hz是回放设置。无平滑、补关节或身份跟踪；三维地面是模型空间参照，未标定房间。实时推理接入、输出工作队列、实板网络、较长真实动作、双路并发及长期验收尚未完成。

最初Codex沙箱内Node创建本地子进程返回EPERM；通过工具执行权限运行本项目子进程后完成实际检查。最初包管理器取自身元数据失败，改为从官方registry下载两个固定运行包并核对SHA512，未安装/升级系统工具。初次渲染的已移除软阴影枚举警告已改用当前PCFShadowMap；无页面运行错误。

## 证据与恢复

- 输入对应、源文件SHA及版本：[archive.json](../../../../software/pc_viewer/data/archive.json)、[依赖锁](../../../../software/pc_viewer/dependencies.lock.json)。
- 本机 `.local/pc-pose-replay-20261018-r1`保留C++可执行文件、原始/收到的768字节、发送日志、`receipt.json`、`preview-check.json`、`browser-values.json`及`runtime.json`；这是本次开发的一套工作产物，不复制旧源码树。
- [validation.json](validation.json)记录阶段验证结果；[preview.jpg](preview.jpg)为真实浏览器画面。
- 预览仅监听127.0.0.1:39380/39381，单次启动默认30分钟自动退出；实际PID和期限以本机runtime记录为准。已发送完毕的C++子进程退出0，只有为用户查看保留的有界本机预览；无板端后台工作。停止/重新打开由本机应用入口管理，不影响EDA作业。
