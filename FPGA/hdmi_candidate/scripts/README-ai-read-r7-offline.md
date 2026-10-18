# r7 离线 bit／ICAP／BOOT 适配候选

这组源码只为新 REF7 的实际 fullflow 结果准备离线封装入口，不修改 `continue_hdmi_reader_idle_candidate.py`、`ai_read_r7_contract.py`、新旧 REF 或原有 r5/r6 算法。本文和本机 mock 均不是候选安装、启动、HDMI 现场验收或重启许可。现场专项暂停和旧 DATA 暂停保持。

## 三个入口

| 文件 | 作用 | 当前默认行为 |
| --- | --- | --- |
| `ai_read_r7_release.py` | 公共纯函数 `routed_release(evidence=None)`、`verify_bit_release(evidence=None)`、`source_closure()` | 无 CLI、无写文件、无工具或设备调用 |
| `continue_hdmi_reader_idle_bit.py` | 独立 bit-only 会话，完整复用 ee11 原厂 bit Tcl、上下文和双派生文件隔离 | 默认 `inspect`；缺实际 r7 formal report 时在 mkdir／工具前拒绝 |
| `package_hdmi_reader_idle_offline.py` | bf39 原有 baseline／ICAP／BOOT／bundle 算法的窄配置适配 | 默认 `inspect`；缺实际 routed/bit gate 时在 mkdir／工具前拒绝 |

未来 root 可分别调用 `continue_hdmi_reader_idle_bit.py inspect`、显式 `bit`，以及封装器的 `inspect`、`icap`、`boot`、`bundle`。这些入口没有执行上板或重启的代码。当前没有实际 r7 release、bit、ICAP、BOOT 或启动包通过；本轮只执行了纯 Python 源码／fixture 检查。

工作根为 `.local/hdmi-live-20261017-r7`，证据根为 `tools/pose-v1/evidence/hdmi-live-20261017-r7`。bit 产物固定 `read-v3r7-bit`，原始 bit 固定新 `reference/fpai_demo_vivado.runs/impl_read_v3r7/ai7030_edif_top.bit`；后处理目录固定 `read-v3-icap`、`read-v3-boot`、`controlled-startup-read-v3`。软件仍严格取 E3 的 `build-read-probe-r2` 和 `read-shared-build-r2`，不是复制到 E7 的旧结果。

## 来源与算法边界

公共 release 固定 fa28 的 r7 contract 和 abb5 的实际 routed wrapper。它重新执行新六阶段 fullflow 身份核验与原 48a 的完整 55 条报告语句，要求当前 formal JSON 与重新计算的完整对象一致，再重读实际原厂／默认 DRC 报告。保留两个既定 AI MinPeriod 原值，不能放宽其它时序或 DRC。新 `impl_read_v3r7` 来源字段始终是 `managed_run:true`；独立 bit 会话仅打开该实际 routed DCP，不运行或伪造 managed run 状态。

bit 入口固定 ee11 的原算法。预检原 21 条语句只移除索引 `[1,8,11,12]` 的旧 r5 阶段／来源断言，由当前 r7 fullflow/formal gate 和显式 routed identity 替换；一处派生输出目录改为 r7。保存完整逆 AST 证明。完整原厂 bit native 原文继续执行原有可逆路径替换及上下文包裹；没有 r6 四参数优化、额外 route、retime、clock-opt 或新豁免。原被动 managed-PS 字节参照只绑定 E3 历史收据，实际设计和输出均指 REF7。

原五个钩子和 `-change_speed FALSE` 必须实际一致；原厂 pre 打开准确 REF7 XPR，返回同一内存设计、器件、`DIRECTORY='.'` 和全部 leaf 名称／类型／LOC／BEL 后才继续。两个原厂派生输出仅重定向到本次 bit/factory-derived，每个只写一次；原位置前后字节必须相同，原始 batch/Tcl 不可作为执行入口。纯 release 再用原函数的 AST 只去掉最后 JSON 写出，重新核对原始 writes/exec 日志与保存 proof，不只相信 `passed` 字段。2768 位索引、endpoint 时序和 clock taps 也在 bit release 重新读取验证。

封装器固定 bf39：20 个精确定位的字符串／布尔常量和两个软件根 `Name` 替换，逐项可逆，完整逆 AST 相等。只替换公开 `Stage.gate` 为新 r7 pure release；原 baseline、Procise 参数、BOOT 7,023,552 字节、非 PL 字节、word-swap/padding、SDK／模型／128 冻结源、epoch 和 tar 成员检查算法保持。BOOT 原算法完成后仅给 review 附加当前 `r7_bit_gate`；后继 BOOT／bundle 须与同一 ICAP／BOOT release 整对象一致。

## 回执契约与源码闭包

`routed_release()` 返回固定键：`formal_review_path/SHA256`、`review_adapter_path/SHA256`、`contract_path/SHA256`、`fresh_fullflow`、`fixed_report_algorithm`、`factory_DRC_profile`（实际键使用 `formal_review_SHA256` 等完整前缀）。两侧 bit-input-proof 与 bit-identity 必须保存完全相同的 `r7_routed_release`。

`verify_bit_release()` 返回 `candidate_run`、`managed_run`、`release_helper_SHA256`、`formal_review_SHA256`、`bit_identity_SHA256`、`routed_checkpoint_SHA256`、`raw_bit_SHA256`、`source_preparation_review_SHA256`、`r7_routed_release`、`factory_derived_isolation`。Host 与 patch/controller 中的 `r7_bit_gate` 直接整对象比较，不忽略未知 bit-identity 字段。

可选 `evidence` 是绝对路径到实际 SHA256 的字典，供调用者将所有实际输入纳入本次阶段冻结。`source_closure()` 给出 15 项实际源码闭包，包含三个新入口及全部固定报告／模板／AST helper／owned supervisor。未来 Host local_review 必须绑定闭包，不能只绑定入口。bit 阶段启动前冻结源码原字节并验证，与保存的 `actual-driver.py`、`actual-supervisor.py`、各 `input-source-*` 和 `source-closure.json` 交叉核验；执行中改源码会关闭后继门。

封装器在首次 pure gate 前冻结自身和 helper 原字节，只编译该 helper 字节，档案也保存同份原值；目录／工具前、工具返回后和最终输入检查前后均重核。工具异常与源码变化同时发生时，保存额外诊断并继续抛出同一个原异常，不能用晚读源码冒充实际执行来源。

bit 使用原 owned supervisor 的 540 秒有界本机阶段；Procise 保持原 180 秒工具预算与 240 秒控制器上限。已有输出目录、原生 bit/marker 或失败会话均拒绝重用。异常先保留执行日志、完整实际源、proof/native 清单和派生原值，不把脚本准备或 SSH／工具退出码单独当整机通过。

## 本机验证证据

E7 `offline-package-preparation-r1` 保留首次 73 项、59.984 秒的实际纯测试结果和旧候选源码；随后增加缺 formal 提前拒绝、raw derived 重新计算、bit endpoint 再核及冻结启动前身份门。

E7 `offline-package-preparation-r2/review.json`：实际 80 项、5.079 秒通过，`process_calls:[]`、`actual_release_pass:false`、`actual_bit_or_ICAP_or_BOOT_generated:false`。包括位置白名单负例、完整逆 AST／native 逆字节、raw 双写与 batch 禁止负例、所有生成模式缺实际 release 拒绝且不创建目标目录，以及明确标记的 bit 回执 unit fixture。源码闭包、原／适配源码、模板与逐项结果完整保存。fixture 不证明真实 Vivado API、时序、bit、BOOT、DMA、推理或 HDMI 通过。

E7 `offline-prepare-postbit-model-r1/review.json`：另有实际 5 项、2.656 秒 pure fixture，直接调用新 `prepare` 和原 factory 算法，只有上游 release/source 使用显式 unit stub。模拟 native bit／marker 和两项正确隔离派生文件出现后，预检严格等于原值；原位置变化则拒绝或使 post-compare 不一致。未触碰实际 REF。

来源冻结修订在 `offline-package-preparation-r4/review.json`：实际 93 项、5.438 秒通过、进程调用为空；其中新增 13 项覆盖冻结原值、归档与编译同份 helper、目录前／工具前后／最终检查时源变化拒绝，以及诊断不覆盖原异常。r2 的三源和 80 项结果原样保留。r3 首轮新增 unit 测试暴露局部变量遮蔽，完整 source／failure 另存且没有 review pass；r4 已修复。此修订只改变新 packager，bf39/ee11、release/helper/bit 源均未改。

随后 `offline-package-preparation-r5/review.json` 实际 103 项、6.093 秒通过，进程调用仍为空。只修公共 helper 的整对象身份比较：使用固定 JSON 排序／分隔符并禁止 NaN，严格区分 bool／int、int／float；增加嵌套 context／clock／endpoint 类型负例及 NaN/Infinity 拒绝。r4 全部证据保留，报告和 BOOT 数学算法不变。

当前源 SHA：release `306d401f30503f34eff8074d4f1bbff68fed4bb2be273b99001fe6e424ac0611`；bit adapter `359752dec92a2eeda16f43237de72546ad46a3e2aae67162f70a024d0fbd2d2c`；packager `23248f1ef75c8c6f25eae9b8c1763d384ba6864e056aff5881b0c9acebf67c23`。
