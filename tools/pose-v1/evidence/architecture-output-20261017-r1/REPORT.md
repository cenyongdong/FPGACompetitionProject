# 新双路展示架构讨论归档

日期：2026-10-17（北京时间）。执行位置：Windows本机；工作目录：`D:/FPGACompetitionProject`。前置：本轮用户明确确认架构并要求先记录讨论；上次项目实施暂停保持。

本批新增`ADR/ADR_49.md`，同步七份现行入口／规范／完成文档。范围仅文档及本目录修订证据，不修改主链源码、模型、SDK、BOOT或构建配置，不进行EDA、板端连接、部署或后台工作。上次封存的板端状态没有在本批重新核验。

`before.json`记录七份现行文档原SHA及大小；六份完整前值在`before-document-edit`，Agents只另存被替换的暂停规则，避免额外复制原文认证资料。`document-revisions.json`记录新旧SHA和说明，新ADR单独标为新增。旧封存报告、旧完成清单及10月16日continuation-state不回写。

`protected-before.json`记录153份既有软件／HDMI源码、构建与锁文件、ADR_00—48及封存入口的核对身份。`verification.json`记录其前后一致性、文档链接及状态断言，`continuation-state.json`记录本轮范围和继续暂停状态。参数中的153是本次本地盘点数量，不代表新增测试用例或实板验证数量。

通过标准：新ADR准确区分已批准架构、候选方向和未完成实施；新增／变更链接可解析；153份被核对文件身份不变；除批准文档外没有运行代码变更。失败停止条件：上述身份、链接或状态断言失败时停止交付并核对，保留原始前值和检查失败，不重写旧记录。

实际检查结果以`verification.json`为准。这里只证明归档与本地身份检查，不能作为HDMI动态帧、PC渲染、网络接口或整机性能通过证据。

格式检查补充：默认`git diff --check`把已有CRLF格式文档新增行的CR报为行尾空白，原输出保留于`format-default.*.txt`；按CRLF文件习惯识别CR后继续检查真实空白，结果见`format-review.json`和`verification.json`。未修改Git配置或进行整文件换行迁移。
