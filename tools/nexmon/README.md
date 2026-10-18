# RT-AC86U Nexmon 准备包

最后实际本地验证：2026-10-17。范围为设备到货前的隔离构建与离线采集验证；**无线实机验证尚未执行**。

## 已完成

| 项目 | 实际结果 | 边界 |
| --- | --- | --- |
| Linux 环境 | 现有 Docker Desktop 上新建隔离 Ubuntu 20.04 镜像、命名卷；每次构建限制 2 CPU／2 GiB | 原 FPAI 镜像、容器和 Lite 未修改 |
| Nexmon CSI | 固定源码实际编译成功，得到 `dhd.ko`、无线固件和 ARM64 静态工具 | 未执行 `install-firmware`，未连接路由器 |
| 驱动独立复核 | 与仓库原始模块等长，仅固定无线固件区域改变；嵌入字节与构建固件完全一致 | 不证明任意原厂系统均可加载 |
| PC 解析 | 14 项单元验证通过；与上游 C 解码在有定义、int32 安全范围比较 14,336 个复数值通过 | 未实现模型的幅度归一化、30 子载波映射 |
| 有界录制 | Linux 回环实际录制 60 个合成 CSI 包，三链 20 组完整，内核丢包 0；拒绝覆盖、无输入超时、超预算拒绝通过 | 回环速率不代表无线性能 |
| 原始样例 | 上游 `example.pcap` 4 包可解析 | 样例是 BCM4358／旧头部，不是 RT-AC86U 实测数据 |

[部署与实机验证方案](DEPLOYMENT-PLAN.md)给出到货后的兼容门检、回退与阶段预算。[本轮证据报告](evidence/preparation-20261017-r1/REPORT.md)记录真实失败、修复和复现入口。芯片调查依据见[先前查证](../csi-planning/RT-AC86U-NEXMON-AUDIT-20261017.md)。

## 环境与产物位置

- Windows 工作目录：`D:\FPGACompetitionProject`。
- 本轮缓存与原始日志：`D:\FPGACompetitionProject\.local\nexmon-rtac86u-20261017-r1`。
- 交付二进制：上述目录的 `delivery`；身份见 `delivery/SHA256SUMS` 和证据目录 `manifest.json`。只从最终 `build-r8`／`capture-r2` 取件，不使用失败目录产物。
- 镜像：`fpga-nexmon-rtac86u:20261017-r3`，ID `sha256:101bab0d9b2f7a5b70133e6611aa5d8ca484046646871efbf78029d605f5be85`。原基础镜像 `ubuntu20.04:custom` 保持。
- 命名卷：`nexmon-rtac86u-20261017-r1`，Linux 树位于 `/work/nexmon`，包含正确软链接的选定源码与工具链。
- 离线检查点：缓存下 `final-audit/linux-build-checkpoint.tar.gz`，包含 Linux 树、Git 元数据、构建日志和兼容头；它不含 Ubuntu 包或整个 Docker 镜像。当前镜像已本地保存，可断网使用；换电脑需另行迁移镜像。
- Windows 下 `nexmon` 是部分 Git 元数据缓存，不能当完整构建树；Windows `nexmon_csi` 是完整 CSI 浅克隆。不要在部分克隆上运行全量 `checkout-index -a`，它会尝试下载其它设备。

固定源：

| 仓库 | 提交 |
| --- | --- |
| [seemoo-lab/nexmon](https://github.com/seemoo-lab/nexmon/tree/68720406f54ff16cad28fd3c51f2392aefad9fb7) | `68720406f54ff16cad28fd3c51f2392aefad9fb7` |
| [seemoo-lab/nexmon_csi](https://github.com/seemoo-lab/nexmon_csi/tree/1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e) | `1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e` |

## 到货时最关键的门检

生成模块的 `vermagic` 是 **`4.1.27 SMP preempt mod_unload aarch64`**，依赖 `bdmf,rdpa_gpl,dpsta,wlcsm,bcmmcast,wfd,emf,igs`。无线补丁目标为 **BCM4366c0／10.10.122.20**，构建版本字符串为 `nexmon.org/csi: 1232-5`。BCM4906 是主 CPU，不能替代无线身份核验。

内核版本相同只是一道门，仍须检查符号、依赖、实际驱动与无线修订。身份不符时停止加载，依据该台设备重新讨论版本路线；不直接把固定偏移应用到用户机器的任意 `dhd.ko`，不预设降级、刷 Merlin 或 OpenWrt。

## 工具接口

- `router/preflight.sh`：只读白名单身份探针，无完整 nvram 导出、无线设置、模块卸载或重启。每条命令独立记录退出值。
- `router/capture_udp5500.c`：路由器侧有界 AF_PACKET 录制器，输出真实以太网 PCAP；ARM64 静态成品已准备。接口和输出路径必须到货后确定。
- `host/csi_verify.py`：经典 Ethernet PCAP 验证，支持明确指定 `current18`／`legacy18`；校验原始发射 MAC、chip marker、链／空间流和整组完整性。`expected-chip=106` 是上游 CSI 包内标记，不是 `wl revinfo` 的芯片编号。
- `host/verify_build.py`：独立检查仓库模块固定固件区域，不连接设备。

本机离线单元验证入口（Windows，项目根目录）：

```powershell
& 'C:\Users\cenyongdong\miniconda3\python.exe' -m unittest discover -s tools/nexmon/host -p test_csi_verify.py -v
```

模型结构、已验收预处理、SDK 和板端帧协议均未改。后续 Nexmon→现有 `[3,3,30,20]` 输入的转换放在独立 PC 适配层；到货一台仅验证一个接收节点，不能冒充原模型的三个独立接收节点。
