# Profiling-off单时钟候选与lazy-r4验证命令

本轮由代理执行，原r2/r3及所有数据保留；已完成阶段不可重跑。原图/RAW/SDK/BOOT和帧同步保持。

## 位置与身份

Windows当前worktree；Python使用`.local/pose-v1-onnx-conda/python.exe`，FPAI现有工具链。
r3包`.local/pose-v1-perf/package-20261007-r3`、构建`.local/pose-v1-build/mixed-20261007-perf-r3`、板端`/tmp/pose-v1-perf/20261007-r3`。
lazy-r4包`.local/pose-v1-perf/package-20261007-lazy-r4`、构建`.local/pose-v1-build/mixed-20261007-lazy-r4`、板端`/tmp/pose-v1-perf/20261007-lazy-r4`。
分别使用`evidence/perf-20261007-r3`和`evidence/perf-20261007-lazy-r4`回传，门禁不能跨包/程序使用。

lazy-r4仅在新副本增加两条字面量错误消息重载，所有原函数、检查和数学运算保留；不是修改原CPU源码、缓存或同步策略。
SDK profiling在两个候选中均为false。单时钟区间保存到monotonic-spans.jsonl，只有最终745/输出就绪证明完成；中间异步返回状态如实保存。

## 板端逐阶段执行

以lazy-r4为例，每条必须在前阶段完成、完整回传、核验并传回对应gate后才执行，不能整段连续粘贴。

```sh
sh -c 'set -eu; cd /tmp/pose-v1-perf/20261007-lazy-r4; sh package/run-perf-validation.sh host-check'
```

Host107上限300秒，仅CPU/Host。通过标准107用例、12注册/Gather保持、22输出与固定参考一致；非法输入拒绝路径保留。
回传完整run-host-check，独立核验后传gates/host-check.acceptance.json。

```sh
sh -c 'set -eu; cd /tmp/pose-v1-perf/20261007-lazy-r4; sh package/run-perf-validation.sh e0'
```

E0上限180秒，308/309/310/308四次全输出与r6逐位一致、首帧重复/CPU实际内容/模型真实参数/1173融合追溯及每帧0→745。
完整回传run-e0，核验后传gates/e0.acceptance.json。

```sh
sh -c 'set -eu; cd /tmp/pose-v1-perf/20261007-lazy-r4; sh package/run-perf-validation.sh p1'
```

上限120秒，3次预热先对照r6后才30次计量；全部33次输出仍逐位一致，profiling关闭，保留各阶段实际等待及单时钟嵌套区间。
完整回传run-p1，核验后生成最终门禁。

## Windows复核

本地原r3 perf_gate.py遗漏stdlib hashlib导入，已保留并另建review_perf_stage.py供应同一标准库绑定；不修改原数据、任何哈希、门禁或计量算法。复现审查使用此入口。

```powershell
$posePy = '.\.local\pose-v1-onnx-conda\python.exe'
$posePackage = '.local\pose-v1-perf\package-20261007-lazy-r4'
$poseBuild = '.local\pose-v1-build\mixed-20261007-lazy-r4'
$poseEvidence = 'tools\pose-v1\evidence\perf-20261007-lazy-r4'
& $posePy tools\pose-v1\review_perf_stage.py --stage host-check --package $posePackage --build $poseBuild --results "$poseEvidence\host-check" --output "$poseEvidence\host-check.acceptance.json"
& $posePy tools\pose-v1\review_perf_stage.py --stage e0 --package $posePackage --build $poseBuild --results "$poseEvidence\e0" --output "$poseEvidence\e0.acceptance.json"
& $posePy tools\pose-v1\review_perf_stage.py --stage p1 --package $posePackage --build $poseBuild --results "$poseEvidence\p1" --output "$poseEvidence\p1.acceptance.json"
```

核验16构建来源、352清单、SDK/程序/前门禁、stdout/stderr/exit/free/dmesg、全输出及区间父子包含/不重叠；CPU桥嵌套区间不能与其父Host跨度再次相加。
后端跨度不等于纯NPU硬件时间。文件输入/批量证据IO、初始化/网络/绘图/编码不计入process_window。
超时/OOM/SDK或总线异常、身份/输出失配即保存停止，不自动重跑、复位、改模型/缓存、减少有效检查或推断整机已通过。
