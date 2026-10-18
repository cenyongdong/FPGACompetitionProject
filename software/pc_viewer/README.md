# PC 三维姿态观察台

独立本地应用：已保存的真实板端结果 → C++ TCP发送器 → Node接收校验 → WebSocket → Three.js三维回放。当前仅验收归档三帧，不创建Engine、不访问板子、不链接HDMI/VPU/SDK。实际结果见[本轮验证](../../tools/pose-output/evidence/pc-replay-20261018-r1/REPORT.md)。

## 模块边界

- `../pose_output/`：C++17拥有值记录、显式小端编解码、带截止时间的TCP发送器和文件回放入口；Windows Winsock／Linux POSIX，无SDK依赖。
- `protocol.mjs`：Node端记录校验、分包重组、序列检查及版本化14关节拓扑。
- `tools/prepare.mjs`：只读原始完整分数/姿态及已验收的候选选择记录。逐字节确认其与HDMI历史回放来源相同，再派生256字节网络记录。不重新推理、不更改旧证据。
- `server.mjs`：仅监听127.0.0.1；启动一次C++发送器，核对每条实际TCP记录，再通过WebSocket发送拥有的骨架值。HTTP `/api/clip` 仅作只读检查。此入口是有界归档演示，尚非通用实板实时服务。
- `public/scene.js`：独立相机、网格、14关节和骨连接。`public/app.js`：来源详情、回放控制与连接状态。不从HTML或静态元数据注入姿态。

现有核心、HDMI应用、RTL、约束、模型和构建入口均不修改。未来接入使用实际 `Result` 的帧号、调用号、`best_index`、分数和 `selected_pose` 拷贝为 `pose::output::Frame`。`TcpSender::send` 是同步有界接口，须由输出工作线程调用；本阶段不声称已有生产者异步队列或双路并发验收。

## 本机运行

从仓库根目录执行；沿用已有Node.js、g++和Windows tar，不安装或升级系统工具：

```powershell
powershell -NoProfile -File software/pc_viewer/setup.ps1
node --test software/pc_viewer/test/transport.test.mjs
node software/pc_viewer/server.mjs
```

已有数据、可执行文件和依赖时只需最后一条。浏览器地址 `http://127.0.0.1:39380`，骨架TCP端口39381；仅本机可访问，不改防火墙。启动会打印URL和PID；Ctrl+C关闭，默认30分钟自动退出。`POSE_HTTP_PORT`、`POSE_TCP_PORT`、`POSE_PREVIEW_MINUTES`可在进程级配置，时限不超过120分钟。检查运行中的传输链：`node software/pc_viewer/tools/check-preview.mjs`。

运行产物集中在 `.local/pc-pose-replay-20261018-r1`：`records.piwpose`、`received.piwpose`、`pose_replay.exe`、发送日志、接收回执和预览验证。Node子进程可能被Codex沙箱拦截；本轮通过工具执行权限运行本项目自己的C++子进程，未放宽系统策略。

## 真实数据与展示语义

`data/archive.json`保留三个来源及其完整原始文件身份；原值仍在旧证据目录维护。帧1000000/1/2对应S11_01_308/309/310，候选槽0，分数分别0.9482421875、0.97900390625、0.96826171875。它们是共享FP16图经ADR_48 v2验收的历史实际输出，不是GT、合成动作或新推理。

三帧均使用既有14关节/14条连接；最高分策略和相同分数取最前槽保持。`score>0.2`不作为发布/人数阈值。全部100分数和4200姿态的旧原始证据继续保留，网络仅发送选中姿态。

展示变换集中在 `scene.js`：`x=C0−1.75, y=4.2−C2, z=−(C1−1.75)`，固定相机观察点，不逐帧居中、不auto-fit、不平滑。坐标详情显示原始C0/C1/C2；小数格式仅用于文字，TCP仍保持FP32位值。地面与圆环是模型空间参照，未作真实房间标定。

默认2姿态/秒是人工设定的回放速度，不是来源采样率或实测推理吞吐。渲染FPS独立采样，播放结束停止；重复播放不产生新推理。归档缺少可靠的采集时间，因此不计算跨主机端到端延迟。服务断开后暂停回放并明确标记断开，已接收原值保留在浏览器内。

## 依赖

固定Three.js 0.186.1及ws 8.22.0，均MIT；版本、官方registry地址和SHA512见 `dependencies.lock.json`。`setup.ps1`下载并验证两个固定包后解压到本模块的 `node_modules/`，不运行安装脚本、不启用可选原生插件。许可证保留于各包的LICENSE文件。运行时所有资源均由本机服务提供，无CDN、云服务或外部字体请求。

官方来源：[Three.js](https://github.com/mrdoob/three.js)、[ws](https://github.com/websockets/ws)。
