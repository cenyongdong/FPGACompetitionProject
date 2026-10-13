# 正式核心重构：原始证据与验证入口

2026-10-13代理实际执行。源码迁移、11组本机、ARM构建、Lite CPU107和三窗口端到端回归完成；未运行60窗口，旧DATA坏读排查继续暂停。

## 结果

| 检查 | 实际结果 | 报告 |
|---|---|---|
| 原身份与范围 | 原锁126、冻结源码/脚本926保持；52份C++核心逐token一致，生产目标仅编译新核心 | [静态](static-review.json)、[映射](source-migration.json) |
| 本机 | 11组原检查器通过；3份CSI/预处理、RGB与RGB565/NV12/NV21新旧逐字节并核原参考 | [本机](native-20261013-r1.review.json) |
| ARM构建 | 56条命令成功；3个演示和11个回归程序；15 SDK头/189厂商身份匹配 | [构建](build-review.json) |
| 已有警告 | 私有need(std::string)未使用；相同选项编译原源码重现 | [原警告证据](original-host-warning.txt) |
| Lite CPU107 | 12注册、22输出、59600 FP32逐位；272.58892371秒，原300秒预算保持 | [CPU完整审查](board/cpu.acceptance.json)、[原回传](board/cpu-return/run-cpu/) |
| Lite三窗口 | 3接收/消费/输出、0覆盖、3不同姿态；308/309/310全部输入/预处理/分数/姿态逐位 | [三窗口](board/short.review.json) |
| 视频 | 354编码及完整离线解码、294实际GUI解码，全3来源/42关节；H264有损不要求RGB逐位 | [视频](board/short.video-review.json)、[实际画面](board/short-contact.png) |
| 退出/资源 | 正常drain/LAST、两STREAMOFF、join后Engine销毁、进程端口回收；规整0、BOOT/SDK/内核相同 | [生命周期](board/short-return/run-short/results/lifecycle.jsonl)、[最终身份](board/final-preflight.json) |

## 完整产物位置

- 当前构建：`D:/FPGACompetitionProject/.local/pose-v1-build/demo-refactor-20261013-r1`，含实际编译源码暂存、SDK快照、14程序、56步完整stdout/stderr及build-result。构建报告的`compiled_not_board_executed`仅描述构建时刻；本页的板端报告记录后续实际执行。
- 本机完整输出：`D:/FPGACompetitionProject/.local/core-refactor/native-20261013-r1`，含命令账本、原/新实现、全部原检查器日志、CSI与像素字节。
- 原CPU107包：`.local/core-refactor/cpu-package`；原308/309/310参考：`.local/core-refactor/reference`。[恢复清单](recovered-inputs.json)逐项绑定从已核实旧工作区复制的字节；旧目录不写入。
- 新板端目录：`/tmp/wifi-pose-demo-refactor-20261013-r1`；本轮已结束，不重复该目录。完整`return-host.tar`、`return-cpu.tar`、`return-short.tar`及解包值、原H264、日志均在本目录`board`内；大二进制保留本机，不以Git中的摘要替代。
- 迁移前锁：[baseline-lock.before.json](baseline-lock.before.json)。旧demo完整副本：[original-demo](original-demo/)；旧文档：[original-documents](original-documents/)。当前源码迁移清单与[文档修订](document-revisions.json)独立保存，不回写2026-10-11完成清单。

## 可复核方法与边界

源码静态检查使用`software/demo/verify_core.py static`；本机检查器在新目录执行旧/新核心，以同一编译器和选项核完整字节。CPU实际链接当前Host适配，测试正文和输入/参考未改；[CPU输入身份](board/cpu-return/run-cpu/input-identities.json)绑定新二进制、构建和原package清单。

三窗口先完成所有原始输出保存，再由`review.py`严格比较；`native_render.py --build`使用本轮锁定渲染来源，`review_video.py`核全部原码流、帧标记和关节。代码布局改变不能外推为故障修复、严格5Hz、永久首启动、长期或HDMI验收。

[实施说明](implementation-notes.json)保留环境门禁、格式化词法门检及已知警告的处理。控制/文档的后续修订单独绑定当前哈希，旧delivery及build-result保持当时身份。
