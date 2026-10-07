# 已批准的逐次Host输入内容取证r4命令

最新结果：当前故障已由代理在新r6身份解决并通过三样本工程验收，见[MIXED-FRAME-STATE-R6-RESULTS.md](MIXED-FRAME-STATE-R6-RESULTS.md)。本文件是历史r4取证命令，不重跑A至H。

**当前停止（2026-10-06）：H已执行并触发不同输入全输出相同门禁，完整回传分析见[MIXED-CONTENT-R4-THREE-FAILURE.md](MIXED-CONTENT-R4-THREE-FAILURE.md)。A至H均勿重跑；下方“现在仅执行H”为执行前历史。r5候选未批准，不执行新的硬件步骤。**

代理已应用批准方案并生成最终身份包，旧r3源码/脚本/程序/三样本失败证据保持。
最新r4单样本内容已独立核验通过，[单样本结果](MIXED-CONTENT-R4-ONE-RESULTS.md)，mixed-one.acceptance.json已生成。
**A至G不要重跑；现在仅执行H传新单样本门禁后一次300秒同Session三样本＋重复首帧内容取证并完整回传。**
下方前置待核验为之前阶段说明；首次Input0内容已确认，连续输入更新仍待取证，旧r3失败保持。
范围[MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md](MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md)，
交付[MIXED-CONTENT-R4-DELIVERY.md](MIXED-CONTENT-R4-DELIVERY.md)。

## A. Windows PowerShell：最终r4包交叉编译

执行位置：本机Windows PowerShell，当前worktree；前置为既有FPAI容器运行，ARM Icraft/CustomOp仍3.39.0。
最终包已经准备，不能重复prepare或改旧manifest凑来源。
开发期间两个未交付中间包content-r4/content-r4-r1保留，不用于构建；只用下面的content-r4-final。

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$posePackage = Join-Path $poseRoot '.local\pose-v1-mixed-validation\package-20261006-content-r4-final'
$poseBuild = Join-Path $poseRoot '.local\pose-v1-build\mixed-20261006-content-r4-final'
& .\tools\pose-v1\Build-MixedValidation.ps1 -Package $posePackage -BuildTag 'mixed-20261006-content-r4-final'
```

目的：用FPAI GCC9.4/CMake3.24.2及/usr/cmake SDK构建独立pose_mixed_check。
12份构建文件含新的content_diagnostic.hpp，20份源身份、15ARM头文件/两库/版本门禁保持。
构建脚本没有新增容器Python需求；不执行二进制/Session/设备初始化或forward。
新BuildTag生成本机及容器新目录，已有目录/非0退出/SDK或来源不符即停，不覆盖/重试/改编译选项。

预期$poseBuild中有pose_mixed_check.arm64、build.log、build-result.json、sdk-audit.json、source/sdk-snapshot。
完整错误和原版本输出缩进warning保留，代理依据日志及哈希审阅；不能凭无红字认定内容取证或问题修复。
完成后通知代理即可主动读取本机文件，构建核验后再提供新目录传输和仅Host命令。

## 后续阶段（当前不执行）

新板端路径预定/tmp/pose-v1-mixed-validation/20261006-content-r4-final，尚未创建/传输。
按构建→Host107＋Host内容路径→离线→SDK内存→apply→单样本→三样本＋首帧重复逐阶段核验，不复用r3门禁。
Host/单/三样本runner会显式加--capture-host-content，其他阶段不启用；硬件仍须显式--allow-device-init。
模型/RAW、CPU内核/Gather、融合组和SDK等待/复制/就绪处理保持；只读取已经在Host CPTR的数据。
Host附加路径包含两个固定模式读回、模拟Input0别名及错期望/未分配/FP16拒绝，不能当真实Session Input0验证。
混合调用每次完整17记录：实际caller_input、Input0返回、八桥暂存输入、七计算结果；最多四次，同Session顺序保持。
实际Caller或Input0与当前帧不符时提前停止并保存原内容，不继续NPU或降低门禁。

所有阶段超时/OOM/总线/SDK异常/存储不明/原门禁失败都保留停止，不自动重试/复位/缓存清理或修改ready。
诊断IO会改变Host时序和分配行为，不作性能结论；若原问题消失仍需讨论受控验证，不能直接宣布已修复。
当前无新ARM取证结果，正常三样本数值报告和后续显示保持暂停。

## B. 新final板端目录创建与四项传输

执行位置：Lite SSH。先取消登录shell的errexit/nounset；创建在独立sh中失败即停，SSH窗口保持。
仅创建不存在的新子目录；返回0才继续传输，非0停止说明情况，不删除/覆盖已有目录。

```sh
set +e
set +u
sh -c 'set -eu; test -d /tmp; mkdir -p /tmp/pose-v1-mixed-validation; test ! -e /tmp/pose-v1-mixed-validation/20261006-content-r4-final; mkdir /tmp/pose-v1-mixed-validation/20261006-content-r4-final; mkdir /tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates'
echo $?
```

Windows PowerShell重新指定全部final路径，避免旧r3或中间r4包变量：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$posePackage = Join-Path $poseRoot '.local\pose-v1-mixed-validation\package-20261006-content-r4-final'
$poseBuild = Join-Path $poseRoot '.local\pose-v1-build\mixed-20261006-content-r4-final'
scp -o StrictHostKeyChecking=yes -r $posePackage 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/package'
if ($LASTEXITCODE -ne 0) { throw 'final包传输失败，停止。' }
scp -o StrictHostKeyChecking=yes (Join-Path $poseBuild 'pose_mixed_check.arm64') 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/pose_mixed_check'
if ($LASTEXITCODE -ne 0) { throw 'final程序传输失败，停止。' }
scp -o StrictHostKeyChecking=yes (Join-Path $poseBuild 'build-result.json') 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/build-result.json'
if ($LASTEXITCODE -ne 0) { throw '构建身份传输失败，停止。' }
scp -o StrictHostKeyChecking=yes 'tools/pose-v1/evidence/mixed-20261006-content-r4/build.acceptance.json' 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/build.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw '新构建验收传输失败，停止。' }
```

四项均成功后才Lite执行C，不拷贝r3门禁或中间r4包。

## C. 仅Host107及纯Host内容路径并回传

执行位置：Lite SSH，外部限时300秒，无Device::Open/Session/NPU。
runner重新核验包、SDK、程序与新构建门禁并显式--capture-host-content。
先原107用例/12注册/22输出，随后纯Host模式读回及别名模拟、错期望/未分配/FP16拒绝；真实Session Input0尚不验证。

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/build.acceptance.json
test ! -e run-host-check
chmod u+x pose_mixed_check
sh package/run-mixed-validation.sh host-check
'
echo $?
```

预期退出0，results/host下107例/22输出保留，另有results/host-content-check.json和content/index.jsonl。
content共五份43200字节记录：两模式各caller/Input0模拟共四正例，以及一份故意错期望但实际Tensor未改的记录。
后者matches_expected=false是Host负例的预期证据，不是混合输入问题；未分配/FP16必须在读之前拒绝。
阶段必须含host_content_paths_completed。退出0仍需代理独立比对模式及全部旧CPU输出，才能生成新Host验收文件。
任一非0/超时/SDK异常保留完整结果回传，不重跑、改捕获参数、覆盖目录或直接离线/硬件。

Windows PowerShell回传全部结果（失败同样回传）：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\host-check'
if (Test-Path -LiteralPath $poseReturn) { throw 'Host回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-host-check' $poseReturn
if ($LASTEXITCODE -ne 0) { throw 'Host结果回传失败，停止。' }
```

完成后通知代理核验，不运行offline/memory/apply/mixed。程序无红字/CPU stdout完成107不能替代附加内容路径核验。

## D. Host验收后仅离线门检

前置：r4 Host107和附加内容路径已独立核验、新门禁已生成；不复用r3门禁。
Windows PowerShell（当前worktree）传新Host验收文件：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$poseAcceptance = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\host-check.acceptance.json'
scp -o StrictHostKeyChecking=yes $poseAcceptance 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/host-check.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw 'Host验收传输失败，停止。' }
```

Lite SSH执行一次；独立sh中的检查失败即停，但保留登录窗口。
30秒内核对真实RAW四参数、三CSI预处理/接口/注册，不初始化设备，不启用内容捕获或完整Session。

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/host-check.acceptance.json
test ! -e run-offline-check
sh package/run-mixed-validation.sh offline-check
'
echo $?
```

预期退出0，保存真实参数、三PS输入和完整SDK/程序/内核日志；退出0仍需代理独立核验才生成离线门禁。
非0/超时/SDK异常保留停止并回传，不重跑/覆盖目录/修改模型或SDK，也不进入memory/apply/mixed。
Windows PowerShell回传整个目录：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\offline-check'
if (Test-Path -LiteralPath $poseReturn) { throw '离线回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-offline-check' $poseReturn
if ($LASTEXITCODE -ne 0) { throw '离线回传失败，停止。' }
```

完成后通知代理读取，真实Session数据更新问题尚未测试，不能据纯Host读回通过宣布修复。

## E. 离线验收后仅SDK内存往返

前置：r4离线已独立核验；确认BOOT/JTAG保持25122301基线且无其他AI/HDMI/视频访问设备。
不能确认则停止说明，不自行结束进程、复位或尝试寄存器访问。
本阶段显式Device::Open，使用SDK默认数据区域分配两个16KiB缓冲区，三组模式共六份回读要求逐位一致。
外部限时30秒，不启用Host内容捕获、完整Session或模型forward。

Windows PowerShell传新离线验收文件：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$poseAcceptance = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\offline-check.acceptance.json'
scp -o StrictHostKeyChecking=yes $poseAcceptance 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/offline-check.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw '离线验收传输失败，停止。' }
```

Lite SSH仅一次；独立sh失败即停，登录窗口保持：

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/offline-check.acceptance.json
test ! -e run-memory-check
sh package/run-mixed-validation.sh memory-check
'
echo $?
```

预期退出0，run-memory-check保存设备/SDK区域、六份回读和完整前后内核日志。
身份/区域/存储不明、非0/超时/OOM/总线/SDK异常均保留停止并回传，不重试/复位/改缓存/SDK或直接apply。
成功只证明SDK CPU↔设备内存复制，不证明模型逐次输入更新或NPU同步。

Windows PowerShell完整回传（失败仍需）：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\memory-check'
if (Test-Path -LiteralPath $poseReturn) { throw '内存回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-memory-check' $poseReturn
if ($LASTEXITCODE -ne 0) { throw '内存回传失败，停止。' }
```

回传后通知代理核验，新memory验收生成并传板前不执行apply/内容前向取证。

## F. 内存验收后一次apply-only

前置：r4内存已独立核验，BOOT/JTAG保持25122301基线且无其他AI/HDMI/视频访问设备。
本阶段显式初始化设备、加载真实RAW、创建/apply混合Session，外部限时300秒；content_capture=false，**不forward**。
创建1181原绑定及部署七实际ZG组完整唯一覆盖1173HardOp、八Host保持和固定成员/同步基线须通过。
不改SDK默认融合、等待/ready/内存优化，不复用r3门禁或重跑旧失败目录。

Windows PowerShell传新内存验收：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$poseAcceptance = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\memory-check.acceptance.json'
scp -o StrictHostKeyChecking=yes $poseAcceptance 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/memory-check.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw '内存验收传输失败，停止。' }
```

Lite SSH执行一次；独立sh失败即停，保留登录窗口：

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/memory-check.acceptance.json
test ! -e run-apply-check
sh package/run-mixed-validation.sh apply-check
'
echo $?
```

预期退出0，阶段original_bindings_validated_before_apply、original_to_effective_bindings_validated和apply_and_bindings_completed_no_forward齐全。
保存两组十快照、1181条追溯记录/汇总、真实参数/输入及完整身份/内核日志；内容目录应未创建。
非0/超时/OOM/总线/SDK异常或绑定基线变化均保留停止，不重试/复位/改缓存、ready或模型。
无论成功或失败都回传，不直接mixed或手工生成apply验收文件。

Windows PowerShell完整回传：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\apply-check'
if (Test-Path -LiteralPath $poseReturn) { throw 'apply回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-apply-check' $poseReturn
if ($LASTEXITCODE -ne 0) { throw 'apply回传失败，停止。' }
```

代理独立核验后再提供新身份单样本内容前向取证命令；apply部署成功不证明Input0消费新帧或r3故障修复。

## G. apply验收后仅308单样本内容取证

前置：r4 apply已独立核验，BOOT/JTAG保持且无其他AI/HDMI/视频竞争访问。
本阶段初始化设备、重新创建/apply同一Session，实际forward仅308/frame6一次，外部限时180秒。
runner显式--allow-device-init、--cases one和--capture-host-content；不改变等待、就绪、缓存或SDK优化。
三PS输入仍作为原固定前检，但309/310不forward；不重跑r3或已验收apply。

Windows PowerShell传新apply门禁：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$poseAcceptance = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\apply-check.acceptance.json'
scp -o StrictHostKeyChecking=yes $poseAcceptance 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/apply-check.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw 'apply验收传输失败，停止。' }
```

Lite SSH仅执行一次；独立sh失败即停但保持登录窗口：

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/apply-check.acceptance.json
test ! -e run-mixed-one
sh package/run-mixed-validation.sh mixed-one
'
echo $?
```

正常预期退出0，保存100分数/4200姿态（400/16800字节）及content/index.jsonl共17条内容记录：
实际caller、Input0返回、五适配节点的八Host暂存输入和七结果，约253760字节。
Caller及Input0必须与当前308输入逐位一致、存储确定为有界Host CPTR FP32，保留same_handle/same_chunk。
若实际数据或存储不符，程序保存已取得证据并提前停止，不继续后续NPU；此时记录少于17条是诊断早停产物，必须原样回传。
任何非0/超时/OOM/总线/SDK异常、非有限输出或原门禁失败即停止，不重试/复位、修改ready/cache或转CPU。
退出0也需独立核对全部内容和执行回调，不据单样本宣布连续输入问题修复、数值或性能通过。

Windows PowerShell回传全部结果（失败同样回传）：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\mixed-one'
if (Test-Path -LiteralPath $poseReturn) { throw '单样本回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-mixed-one' $poseReturn
if ($LASTEXITCODE -ne 0) { throw '单样本回传失败，停止。' }
```

代理主动分析实际内容及原输出，核验后才给同Session三样本内容诊断命令；当前不执行mixed-three。
诊断文件IO会改变时序/分配行为，不作持续性能或自动修复结论。

## H. 单样本验收后三样本及重复首帧内容取证

执行前置：r4单样本已独立核验，BOOT/JTAG保持，未启用其他AI/HDMI/视频竞争访问。
本阶段外部限时300秒，创建/apply一次Session，按308/frame6、309/frame7、310/frame8、308/frame6顺序执行四次forward。
invocation为0/1/2/3；runner显式--allow-device-init、--cases three和--capture-host-content。
不修改等待、ready、缓存、SDK优化或模型参数，不在各帧之间重建Session。

Windows PowerShell传新单样本门禁（本机当前worktree）：

```powershell
$poseRoot = 'C:\Users\cenyongdong\.codex\worktrees\dea3\FPGACompetitionProject'
Set-Location -LiteralPath $poseRoot
$poseAcceptance = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\mixed-one.acceptance.json'
scp -o StrictHostKeyChecking=yes $poseAcceptance 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/gates/mixed-one.acceptance.json'
if ($LASTEXITCODE -ne 0) { throw '单样本验收传输失败，停止。' }
```

Lite SSH执行一次；独立sh保存停止条件，不令登录窗口因test失败退出：

```sh
set +e
set +u
sh -c '
set -eu
cd /tmp/pose-v1-mixed-validation/20261006-content-r4-final
test -f gates/mixed-one.acceptance.json
test ! -e run-mixed-three
sh package/run-mixed-validation.sh mixed-three
'
echo $?
```

正常预期退出0，四次caller/Input0均与各自当前固定参考逐位一致；每次17份内容，共68条，捕获1015040字节。
三份完整分数/姿态及重复首帧结果必须有限，重复308逐位一致，不同CSI不能全部输出相同。
保留每次七ZG/六计算Host回调、桥事件、invocation、完整绑定/身份/内核日志。
若内容失配提前停止，记录少于68条属于取证结果；不得补跑以凑齐记录。
超时、非0、OOM、总线/SDK异常、非有限、输入失配、全部输出不变或基线变化均保存停止，不自动重试、复位或改ready/cache。
成功也不自动宣布r3修复、精度或性能通过；诊断会改变时序，必须独立分析后讨论。

Windows PowerShell完整回传，无论成功还是失败：

```powershell
$poseReturn = Join-Path $poseRoot 'tools\pose-v1\evidence\mixed-20261006-content-r4\mixed-three'
if (Test-Path -LiteralPath $poseReturn) { throw '三样本回传目录已存在，保留停止。' }
scp -o StrictHostKeyChecking=yes -r 'root@192.168.126.49:/tmp/pose-v1-mixed-validation/20261006-content-r4-final/run-mixed-three' $poseReturn
if ($LASTEXITCODE -ne 0) { throw '三样本回传失败，停止。' }
```

回传后由代理核对每个边界的实际字节变化，定位首次不符合预期的位置；不手工生成验收、不继续显示或连续性能测试。
