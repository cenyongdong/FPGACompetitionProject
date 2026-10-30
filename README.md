# 基于 Wi-Fi CSI 的嵌入式多人三维姿态感知系统

## 一、作品介绍

本作品面向高隐私性智能家居，通过 Wi-Fi 信道状态信息（CSI）感知人体动作，在悟净 Lite 平台完成多人三维姿态推理与显示。系统无需摄像头或人体穿戴设备，以三维骨架呈现活动，为居家活动观察、健身交互等应用提供感知基础。

系统采用 PS、NPU 与 PL 协同实现：PS 负责输入整理、预处理和姿态后处理，NPU 执行模型推理，PL 负责本地 HDMI 显示。PC 网页作为可选观察端，支持三维视角交互；板端推理和本地显示可以独立运行。

```text
实时 CSI 采集 ──┐
               ├─→ PS 预处理 → NPU 姿态推理 → PS 筛选、跟踪与滤波 ─┬─→ PL / HDMI
板端官方 CSI ──┘                                                └─→ 可选 PC 三维网页
```

两种输入互斥，共用同一套预处理和推理链。官方数据模式在板端读取转换后的原始 CSI 并逐帧推理；当前演示包按 **1 人约 10 秒 → 2 人约 9 秒 → 3 人约 9 秒** 顺序展示。模型采用原 epoch99 的 180-query 部署图，输出最多三人、每人 14 个关节，使用 TopK=3 和严格 `score > 0.2` 筛选。

本仓库保存当前软件核心、FPGA 工程、模型适配工具、部署交付及开发记录。阅读源码从 `software/pose180_pipeline/` 开始；直接部署从 `Deliverables/` 开始。项目已完成有限实板演示与交付收尾，具体实测范围见 [PROJECT-PROGRESS.md](PROJECT-PROGRESS.md)。

## 二、目录与文件职责

### 2.1 仓库目录

| 位置 | 职责 |
|---|---|
| [software/pose180_pipeline/](software/pose180_pipeline/) | **当前主工程**：板端核心、输入控制、PC 页面、测试及构建打包入口 |
| [FPGA/hdmi_candidate/](FPGA/hdmi_candidate/) | HDMI 硬件工程；`rtl/`、`constraints/`、`scripts/`、`sim/` 分别保存逻辑、约束、构建脚本与仿真，发布配置按恢复说明及对应记录核对 |
| [Deliverables/](Deliverables/) | **演示部署包和核心源码快照**；`hardware/` 为硬件交付，`history/` 为历史软件与模型归档 |
| [model/](model/README.md) | 当前部署 JSON／RAW、源 ONNX、转换配置与模型说明已放行；训练 checkpoint 和中间产物留在本机，获取与使用方式见模型索引 |
| [tools/](tools/) | 模型训练、转换、采集、验证与故障分析工具；带日期的取证目录按所属历史阶段阅读 |
| [Docs/commit_docs/](Docs/commit_docs/) | 技术文档、海报等提交材料；`Docs/` 其余部分主要为厂商资料与开发参考 |
| [CompetitionDescription/](CompetitionDescription/) | 比赛选题指南等本机参考资料 |
| [ADR/](ADR/) | 架构决策、接口设计和技术说明 |
| [software/core/](software/core/)、[demo_v1/](demo_v1/) | 早期共享实现与旧演示工程，保留用于追溯；当前 180-query 核心维护位置见下表 |
| `.local/`、`Logs/`、`tmp/` | 本机验证证据、运行日志和临时产物，不作为常规 Git 交付内容 |

### 2.2 部署包与提交文件

| 文件或目录 | 用途 |
|---|---|
| [pose180-three-clips-20261029-r3-final.tar.gz](Deliverables/pose180-three-clips-20261029-r3-final.tar.gz) | **最新完整演示部署包**，约 36.5 MB；含板端程序、模型、三段官方 CSI、PC 服务及启动脚本 |
| [部署说明](Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md) | 板端解压、预检、启动、停止、重启条件及 PC 有线连接步骤 |
| [部署包 SHA-256](Deliverables/pose180-three-clips-20261029-r3-final.tar.gz.sha256) | 传输后核对压缩包完整性 |
| [交付核验记录](Deliverables/pose180-three-clips-20261029-r3-final.validation.json) | 打包核验、已有同内容板测及 PC 本地检查结果 |
| [pose180-core-sources-final-20261029.tar.gz](Deliverables/pose180-core-sources-final-20261029.tar.gz) | **核心源码交付快照**；日常修改仍在 `software/pose180_pipeline/` 进行 |
| [源码快照 SHA-256](Deliverables/pose180-core-sources-final-20261029.tar.gz.sha256) | 核对源码归档完整性 |
| `Deliverables/pose180-three-clips-20261029-r3/` | 本机已解压演示目录；克隆仓库后可自行解压上述部署包生成 |
| [技术文档排版修订版](Docs/commit_docs/技术文档_v1_排版修订.docx) | 当前排版修订稿；[技术文档 v1](Docs/commit_docs/技术文档_v1.docx) 保留用户编辑版本 |
| [项目海报](Docs/commit_docs/项目海报.pdf) | A1 竖版作品海报 |

部署包解压后的关键位置如下，路径均相对于包根目录：

| 包内位置 | 职责 |
|---|---|
| `board/models/` | 板端推理模型 |
| `board/dataset.piwcsi2`、`board/dataset.json` | 官方 CSI 数据及片段来源、顺序清单 |
| `board/runs/` | 本次运行生成的日志与状态 |
| `check.sh`、`prepare-boot.sh` | 运行前核对及下一次启动凭据准备 |
| `start-dataset.sh`、`start-live.sh` | 官方三片段顺播与实时采集两个启动入口 |
| `stop.sh`、`status.sh` | 正常结束与关闭状态核验 |
| `start-pc.ps1` | Windows PC 观察服务入口 |

### 2.3 当前核心源码

**核心源码集中在 [software/pose180_pipeline/src/](software/pose180_pipeline/src/README.md)，程序入口是 [app/main.cpp](software/pose180_pipeline/src/app/main.cpp)，正式构建目标为 `pose180_demo`。** 同一模块的头文件与实现文件放在同一目录中。

| 模块或文件 | 职责 |
|---|---|
| [src/app/](software/pose180_pipeline/src/app/) | 参数解析、输入选择、推理线程与程序生命周期 |
| [src/common/](software/pose180_pipeline/src/common/) | 公共数据结构、最新窗口、固定缓冲和帧协议 |
| [src/input/](software/pose180_pipeline/src/input/) | `csi.cpp` 接入实时 CSI，`dataset.cpp` 读取官方数据；`nexmon/` 负责解码、三 RX 组窗和重连 |
| [src/preprocess/](software/pose180_pipeline/src/preprocess/) | 幅度与相位预处理，将复数 CSI 转为 `[1,180,60]` FP32 特征 |
| [src/inference/](software/pose180_pipeline/src/inference/) | SDK 与模型资源管理、推理、输出读取和在途资源释放保护 |
| [src/pose/](software/pose180_pipeline/src/pose/) | 候选筛选、去重、人物关联及 CPU 姿态滤波 |
| [src/display/](software/pose180_pipeline/src/display/) | 骨架投影、RGB565 绘制、HDMI 帧交接和停止排空 |
| [src/io/](software/pose180_pipeline/src/io/)、[src/diagnostics/](software/pose180_pipeline/src/diagnostics/) | 独立网络消费者、状态发布与有界异步日志 |
| [src/compat/](software/pose180_pipeline/src/compat/) | 旧严格链和历史硬件配置的兼容声明 |
| [control/](software/pose180_pipeline/control/README.md) | Python 启停控制、双输入配置、数据准备及路由器服务 |
| [host/](software/pose180_pipeline/host/README.md) | Node.js 观察服务、`web/` 三维页面和 PC 测试 |
| [tests/](software/pose180_pipeline/tests/README.md) | 原生模块测试、Nexmon 测试和 SDK 接口替身 |
| [tools/](software/pose180_pipeline/tools/) | 构建、打包与离线检查工具 |
| [CMakeLists.txt](software/pose180_pipeline/CMakeLists.txt) | 当前 C++ 工程统一构建入口 |
| [resident/](software/pose180_pipeline/resident/) | 演示使用说明、分阶段验证与历史运行记录 |

### 2.4 根目录文档

| 文件 | 职责 |
|---|---|
| [README.md](README.md) | 作品介绍、目录职责和交付入口 |
| [PROJECT-PROGRESS.md](PROJECT-PROGRESS.md) | 项目完成情况、最终配置、实测范围和恢复入口 |
| [DIFFICULTIES.md](DIFFICULTIES.md) | 开发难点、处理方法及工程收口说明 |
| [DOCUMENTATION.md](DOCUMENTATION.md) | 完整 Markdown 导航与历史文档分类 |
| [Done.md](Done.md) | 分阶段成果及开发参考 |
| [REFERENCES.md](REFERENCES.md) | 资料索引与阅读记录 |
| [Agents.md](Agents.md) | 本地工程执行规则与授权边界 |
| [.gitignore](.gitignore) | Git 提交范围，采用指定交付文件放行规则 |

## 三、部署与演示入口

板端使用 ARM64 Lite、匹配的已发布 BOOT、Icraft/customop 3.39.0 和 Python 3。可选 PC 观察端需要 Node.js 20 或以上；包内已带网页资源，无需 `npm install`。完整操作以 [部署说明](Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md) 为准。

1. 将最终部署包解压到独立目录；板端推荐位置为 `/root/pose180-three-clips-20261029-r3`。
2. 按部署说明核对设备状态、BOOT 和启动资格，再执行所选输入的 `check.sh`。
3. 如需 PC 展示，先运行 `start-pc.ps1`，指定实际可达的板端地址及本机有线地址，打开 `http://127.0.0.1:39380/`。
4. 板端执行 `sh start-dataset.sh` 顺序展示三段官方数据，或执行 `sh start-live.sh` 开始实时采集；两个入口不能并发运行。
5. 数据集到末尾自动结束，实时模式通过 `sh stop.sh` 正常结束，再用 `sh status.sh` 核对关闭状态。

三段片段共用同一次 SDK 生命周期，片段之间无需重启。当前硬件每次 FPGA 配置只允许消费一次功能启动入口，完整结束后再次启动推理或切换输入，须按部署说明准备凭据、正常重启并重新预检。`prepare-boot.sh` 只核对启动文件和准备凭据，不写 BOOT，也不自行重启；单独重启 PC 服务不需要重启开发板。

## 四、进一步阅读与维护

- 了解数据流、模块接口和资源所有权：阅读 [技术说明](ADR/TechDetails.md) 与 [ADR 索引](ADR/README.md)。
- 修改当前软件：从 [核心模块索引](software/pose180_pipeline/src/README.md) 开始，再阅读 [测试入口](software/pose180_pipeline/tests/README.md) 和 [最终审查记录](software/pose180_pipeline/resident/FINAL-REVIEW.md)。
- 查看硬件发布、设备状态和恢复步骤：阅读 [RESUME.md](FPGA/hdmi_candidate/RESUME.md)。历史运行状态不等于设备当前在线状态。
- 查看展示片段的来源和范围：阅读 [三片段清单](software/pose180_pipeline/resident/DATASET-PLAYLIST.md)。

Git 提供当前完整演示包、源码快照及其校验文件、部署说明、选定技术文档与海报，以及当前模型的 ZG JSON／RAW、源 ONNX、转换配置、选题指南和指定验证报告。大尺寸训练 checkpoint、解压副本、旧包、原始采集、模型中间产物、SDK 安装资料、日志和构建缓存继续保留在本机；因此部分历史附件需要完整开发工作区才能打开。文件范围与文档检查说明见 [完整导航](DOCUMENTATION.md#git-克隆后的文件可用范围)，训练权重的获取方式见 [模型说明](model/README.md#本机保留的开发产物)。

已有同一 r3 板端内容完成 420 帧新推理、HDMI 采纳与 PC 发送，并正常退出；最终 PC 修订另有本地检查。有限演示、长期运行和数值精度分别记录，完整验证边界统一见 [项目进度](PROJECT-PROGRESS.md)，不在本页重复维护。
