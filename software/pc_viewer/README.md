# PC 三维姿态观察台

**版本定位（2026-10-29）：** 本页保留早期工程、兼容接口或对应批次结果，文中的“当前”只指该版本。现行 180-query 主链在[主工程](../pose180_pipeline/README.md)，运行及验收范围见[最终进度](../../PROJECT-PROGRESS.md)；旧命令不作为最新部署入口。

独立本地链路：已保存真实板端结果 → SDK无关C++发送器 → TCP → Node接收校验 → WebSocket → Three.js。现已接入60个不同的历史结果，默认循环预览可从[本地地址](http://127.0.0.1:39380/?play=1&loop=1)打开。实际验证与边界见[本轮记录](VALIDATION-20261018.md)。不创建Engine、不访问Lite、不链接HDMI／VPU／SDK。

## 长动作素材

来源是2026-10-11原演示成功运行保存的 `frames.jsonl` 中的完整精度 `selected_pose` 和 `best_score`，并与当时主机输入目录、实际发送清单、板端成功摘要关联。60份输入和60个选中姿态均不同，坐标均精确表示为FP32。原始完整100候选数组在当前可用目录中未找到，因此本轮不声称重新检验了全部候选或模型精度。

| 片段 | 原始样本 | 原始帧号 | 数量 | 首末记录间隔 |
|---|---|---|---:|---:|
| S11_01 | 308–324 | 1000000–1000016 | 17 | 8.010秒 |
| S11_02（默认） | 301–343 | 1000017–1000059 | 43 | 21.001秒 |

两个源序列独立选择，播放／拖动／循环都不跨片段接续。播放节奏使用当时同一主机的实际发送时间差，默认约2姿态/秒；这不是原始RF采样率或实测模型吞吐。渲染FPS另行采样。循环和插看不会增加真实结果数。

长素材来自原演示模型，界面单独标注；先前三帧共享FP16素材的来源信息继续保留在 `data/archive.json`，不与本批混为同一数值验收。原演示仅前三份有旧参考逐位检查，另外57份历史范围为形状／有限性／选择／映射；本轮不扩大该范围。

## 模块边界

- `../pose_output/`：原有C++17拥有值协议与同步有界发送器未修改，复用相同来源的已验证本机可执行文件。
- `tools/prepare-demo.mjs`：只读导入原始JSON选中结果、时间与来源；检查FP32精确性、唯一性和源片段，生成网络记录与 `data/demo60.json`。不重新选择候选或新增阈值，不修改旧证据。
- `protocol.mjs`：PIWPOSE1版本1编解码／分包／顺序检查未修改。
- `public/playback.js`：无DOM／渲染／网络依赖的片段边界和回放时序。
- `public/app.js`：片段、逐帧、进度、原速／半速／倍速、循环、原值详情；默认一次播放，URL `?play=1&loop=1`明确请求自动循环。
- `public/scene.js`：既有Three.js三维渲染保持。固定14关节拓扑和模型坐标变换，不auto-fit、不平滑、不增加身份跟踪或额外关节。
- `server.mjs`：仅127.0.0.1监听；启动一次C++发送器，逐记录核对实际TCP字节，再经WebSocket交付。HTTP `/api/clip`供只读检查。

HDMI源码／RTL／约束／构建、正式推理核心、模型／SDK／BOOT和CSI／显示IPC均不修改。未来实时接入仍只通过拥有值Result适配；发送器应在独立输出线程使用。本阶段未完成实时发布、双路并发或长期验收。

## 运行与恢复

在仓库根目录执行；已准备的本机环境直接启动即可：

```powershell
node software/pc_viewer/server.mjs
```

本机HTTP39380、骨架TCP39381，默认30分钟自动退出，可用Ctrl+C结束。环境变量 `POSE_HTTP_PORT`、`POSE_TCP_PORT`、`POSE_PREVIEW_MINUTES`仅作用当前进程；期限不超过120分钟。`POSE_DEPENDENCY_ROOT`可指向已有固定依赖目录，只读复用并校验版本，适用于独立worktree。

新环境需要已保存的真实证据目录，当前找到的位置为 `D:/FPGACompetitionProjectB/tools/pose-v1/evidence/demo-20261011-r4`：

```powershell
powershell -NoProfile -File software/pc_viewer/setup.ps1 -ArchiveEvidence D:/FPGACompetitionProjectB/tools/pose-v1/evidence/demo-20261011-r4
node --test software/pc_viewer/test/transport.test.mjs
node software/pc_viewer/tools/check-preview.mjs
```

`setup.ps1`沿用已有Node.js／g++／tar，下载核对两个固定运行包，不安装或升级系统工具；原始资料与当前worktree可以分开。只重新导入可用 `node software/pc_viewer/tools/prepare-demo.mjs <证据目录>`。首次导入路径保存在manifest，之后可不带路径复用。

一套运行产物集中在 `.local/pc-pose-replay-20261018-r2`：原始／接收记录、发送器、日志、回执、网络检查、运行PID／期限及实际接收快照。输入／包身份见 `data/demo60.json`；不维护源码全树哈希。

## 预览与限制

[43帧动作动画](previews/s11-02-motion.gif)由实际TCP接收快照独立绘制，使用相同原坐标和拓扑，用于直接观看动作变化，**不是Three.js浏览器录像或截图**。交互3D需打开本地预览。本轮浏览器自动化连接持续超时，未新增浏览器截图／交互复核；后端传输、前端语法及片段时序测试均已完成，渲染模块沿用此前已验证实现。

固定依赖Three.js0.186.1、ws8.22.0，均MIT；来源与SHA512见 `dependencies.lock.json`，许可证保留于包中。运行不请求云服务、CDN或外部字体。科学数据动画使用已存在的Pillow／NumPy；来源数据和回放都未平滑或修补。
