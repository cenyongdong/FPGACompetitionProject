# Nexmon 环境准备与离线验证报告

日期：2026-10-17。用户已决定先购买一台原厂 RT-AC86U，并要求代理先准备部署环境和采集验证方案，设备到货后再实测。本轮**离线构建和工具验证通过，路由器实测未执行**。

## 执行位置、资源和来源

Windows `D:\FPGACompetitionProject`；已有 Docker Desktop 原先未运行，本轮隐藏启动，未安装或替换既有 Docker。命名容器／镜像／卷均以 `nexmon` 或 `fpga-nexmon` 区分，未运行或修改 FPAI 容器，未连接 Lite、路由器或 RF 发射设备。旧 DATA 和其它板端任务未恢复。

基础镜像原 ID 为 `sha256:397a49458ae85e065c484eaa3a83d4b5cc248f78bdf6a534e2414ce275e591db`，新镜像 r1／r2／r3 逐层安装缺失依赖，原镜像不变；最终身份见 [manifest.json](manifest.json)。新环境内包含主机 GCC 9.4、AArch64 GCC 9.4 和上游 ARM Embedded GCC 5.4.1（20160609）。无线固件是 ARMv7-R 目标；路由器 Linux 驱动／工具是 AArch64，两种目标不能混用。Python 2 只在隔离容器用于上游旧构建脚本，Windows Python 保持原样。

选定 Nexmon 和 CSI 源提交见 [README](../../README.md)。完整选定 Linux 构建树位于本轮命名卷，已另存可读的 79,187,869 字节 `linux-build-checkpoint.tar.gz`；该归档包含 Linux 源码、软链接、Git 元数据及构建状态，不是整机 Docker 镜像导出。最终构建在断网容器内、2 CPU／2 GiB、单线程 CSI make 下成功，未运行安装目标。

## 实际验证与证据

| 验证 | 实际结果 | 原始证据 |
| --- | --- | --- |
| 最终固件／模块／工具构建 | exit 0，`OFFLINE_BUILD_COMPLETE=1`；`dhd.ko` 1,724,632 字节、固件 1,111,247 字节，ARM64 静态 nexutil／makecsiparams | [最终完整 stdout](logs/firmware-build-r8.log)、[上游原生日志](firmware-native-log) |
| 模块独立比较 | 8 项全部符合：ELF64 AArch64、等长、前后区域未变、固件区域准确替换且确实变化、预期 vermagic | [module-verification.json](module-verification.json)、[核验代码](../../host/verify_build.py) |
| ABI 元数据与补丁版本 | `4.1.27 SMP preempt mod_unload aarch64`；补丁版本 `1232-5`，依赖完整保留 | [audit.log](audit.log) |
| PC 解析单元验证 | 14 项，0.105 秒，全部通过；包含缺链、重复、混序列、chip 不符、全零、截断、分片、预算和格式 | [host-tests-r3.log](logs/host-tests-r3.log) |
| 官方 C 对照 | 安全移位／int32 范围内 14,336 个复数值一致；上游旧格式样例 4 包解析通过 | [upstream-reference.json](upstream-reference.json)、[完整日志](logs/reference-check-r1.log) |
| 录制器实际回环 | 60 包、19,944 字节、20 个三链组；0.414988 秒、kernel_drops 0；现有输出拒绝、无输入 1.177061 秒退出、61 秒预算拒绝 | [loopback-result.json](loopback-result.json)、[完整日志](logs/capture-loopback-r1.log) |
| 参数与脚本 | 真实工具输出解码 34 字节、示例 chanspec 0xd024、core mask 7、stream mask 1、源 MAC 一致；shell 语法检查及归档完整读取通过 | [参数检查](parameter-verification.json)、[原文](syntax-params-archive.log) |
| 资源回收 | 本轮已停止容器删除，无运行中任务容器；原 FPAI 保留停止状态，新镜像及命名卷保留供到货使用 | [清理记录](container-cleanup.txt)、[结束状态](containers-after.txt) |

回环是本机内核、合成载荷和实际录制器的联合检查，不能当 RT-AC86U RF 测试、300 Hz 采样或模型推理证据。上游样例是 BCM4358，不能当本机目标的实测样本。C 对照不覆盖上游定义外的大移位／溢出，也不涵盖 MATLAB AGC 或原工程预处理。

最终二进制位于 `.local/nexmon-rtac86u-20261017-r1/delivery`；[SHA256SUMS](delivery-SHA256SUMS) 与 [manifest.json](manifest.json) 区分二进制、检查点和源码身份。原驱动库文件仅供构建对比，不能替代到货机器本身的备份。

## 失败、修复和保留边界

所有失败 stdout 保留在 [logs](logs)；后续新运行不覆盖旧记录。

- 初始普通沙箱访问 Docker／WSL 受限，随后授权通路确认 Desktop 未运行并启动；没有把最初 E_ACCESSDENIED 当作 Docker 未安装。
- 首次 Dockerfile 把本地 image ID 用作 FROM 引用而被当作仓库名；改用已有 tag 后构建。随后分别补上 b43 assembler 的 `libfl-dev`、上游脚本所需 Python 2，形成 r1→r2→r3 隔离镜像。
- Windows 部分克隆 checkout 与软链接不完整；复制元数据到 Linux 卷按设备稀疏路径取件。首次 `checkout-index -a` 意外请求其它设备、断网失败；改为明确稀疏物化，不下载无关芯片，不把 Windows 元数据树当完整来源。
- 固件 build-r2 假设 cc1 在 libexec，实际在 lib/gcc；r4 遇上游并行 init 缺 log/gen；r5 工具链 target-bin 未选入而误用主机 as；r6 发现 Python 2 缺失。分别修正实际路径、`make -B -j1`、目标 assembler 路径和隔离依赖，r8 固件构建最终通过。旧失败不是无线故障，未在设备重试负载。
- r7 固件成功但 ARM64 nexutil 缺 `argp-extern.h`；r8 只增加私有构建 include，并预包含 `uint` typedef，未改上游正式源。makecsiparams 的初始独立编译先后缺 `bcmwifi_channels.c`、`-I.`，均保留失败，新运行成功。
- Python 3.14 的 TemporaryDirectory ACL 与沙箱不兼容，前两轮离线测试未能读取自己创建的安全临时目录；改为工作区中 UUID 新目录继承 ACL，r3 全部 14 项通过。不是修改数值断言使其通过。

保留的真实编译警告：`nexutil` raw 输入未检查 fread；整数模式缺值存在空指针传入 strtoul 路径；Broadcom 头在 AArch64 有 uintptr 宽度转换告警。已保存上下文，未消除原警告或宣称所有选项可靠。后续只走经过解码长度检查的显式 Base64 CSI setter；不使用省略值的 `-i` 或 raw stdin。参数工具非法信道实际返回 0，已单独复现并记录，部署须检查结果内容而非仅看退出码。若受控路径仍报错，保存并停止，不能按警告已知而放宽验收。

## 复现与恢复入口

原生日志为沿同一隔离构建树追加保存，可能包含前轮诊断，不能假定每个文件只含 r8。`error.log` 保留一条首次生成 `gen/nexmon.pre` 前 cat 文件不存在的信息：上游规则先 cat→awk 创建该文件，再由 GCC 插件写入；其 pipeline 未启用 pipefail。`linker.err` 的 706 行均为 `--print-gc-sections` 的 unused section 删除信息，非 706 个链接错误。原文均保留；最终 r8 stdout、编译／链接退出码、补丁无 reject、固件区域独立复核组合支持本次离线构建通过，不能用日志文件名当通过或失败结论。

现有本地镜像和命名卷已准备，可断网重建。使用新输出目录、新容器名，将命名卷挂到 `/work`，本轮缓存只读挂到 `/input`、`tools/nexmon` 只读挂到 `/kit`，新输出挂 `/out`，传入 `NEXMON_PREPARED=1`，在 r3 镜像执行 `bash /kit/environment/build.sh`。每次限制 2 CPU／2 GiB；构建脚本不会安装固件。CSI 上游生成版本计数会随构建变化，**重建必须生成新清单，不能期待 r8 哈希不变**。

若命名卷丢失，可把校验后的 Linux 检查点解包到新卷 `/work`，再用本地 r3 镜像；不能把归档直接展开到 Windows 并假定软链接及权限仍正确。当前镜像只有本机副本，换电脑还需迁移镜像，不依赖设备到货时重新下载依赖。

已通过适当离线验证后停止扩大测试。下一步依据[实机方案](../../DEPLOYMENT-PLAN.md)，等待设备到货，由只读身份核验开始；无线采集、原驱动恢复、受控发射、三接收节点同步和模型接入尚未通过。固定模型、SDK、BOOT、帧协议及旧 DATA 暂停均保持。
