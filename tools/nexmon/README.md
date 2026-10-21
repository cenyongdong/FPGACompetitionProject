# RT-AC86U Nexmon 准备包

最后实际验证：2026-10-20。**现有蛟龙16pro的MT7922已在5.745 GHz／20 MHz完成20秒300 Hz受控发包，RT-AC86U收到真实三链CSI；独立、均匀300 Hz CSI仍未验收。** 本轮模型结构、预处理、SDK及板端协议均未修改，未进行模型推理。

## 10月20日5 GHz受控采样

实际成功路径：笔记本MT7922 → 自有手机`c_iPhone`的5 GHz热点；RT-AC86U在信道149／20 MHz旁路接收。两台电脑的管理连接均走路由器有线LAN。数据发往手机热点网关`172.20.10.1:39031`，手机未运行UDP接收器，因此没有端到端UDP槽位投递台账，不能把零条主机接收台账解释为丢包。完整事实与恢复入口见[本轮汇总](evidence/5ghz-300hz-20261020-r1/run-summary.json)。

| 检查 | 实际结果 |
| --- | --- |
| 频段与制式 | 信道149／5.745 GHz、20 MHz、802.11ac；RT-AC86U为一个独立接收节点，选core 0／1／2及stream 0 |
| 低速预检 | 50 Hz／2秒，100次发送全部完成；306条CSI、102个完整身份组，无缺链或重复，内核丢包0 |
| 300 Hz／20秒发射 | 6,000／6,000次计划发送全部执行，无漏槽；间隔p50为3.3333 ms、p99为3.4004 ms、最大6.1278 ms |
| 真实CSI | 26.039905秒录制18,606条CSI，内核丢包0；保留为[原始PCAP](evidence/5ghz-300hz-20261020-r1/phone-burst20.pcap) |
| 严格身份校验 | false：6,010个完整身份组、576条重复core身份记录、缺链组0；不放宽原规则或删除重复使其通过 |
| 原始事件导出 | [NPZ](evidence/5ghz-300hz-20261020-r1/node-events/node-events.npz)为`[6202,3,64]`，含192个重复身份事件，`model_ready=false`；[全窗时序](evidence/5ghz-300hz-20261020-r1/node-events/summary.json)的事件间隔p50／p99为3.32594／4.14109 ms |

发送调用完成、CSI记录数及接收端OS时间均不证明独立RF帧或均匀3.333 ms空口采样。完整录制包含发射前后背景及空闲区间，不能用全窗最大间隔直接诊断发射期停顿；重复身份仍可能涉及重传、聚合或QoS序号，但当前头部缺少足够证据区分。尚未实现逐UDP槽位→无线帧→CSI的对应、AGC／相位标定、物理30子载波映射及三个独立节点同步。

本轮保留了实际失败：台式机热点接口报告不支持5 GHz；此机Merlin-KoolShare 386.9＋既有Nexmon模块兼作WPA2接入点时，笔记本关联后约5秒断开，未据此推断所有Nexmon接入点均不支持；台式机也未成功接入手机5 GHz热点，因此最终采用向自有手机网关发包。校园网数据目标切换命令被自动审批拒绝，原因为`blocked by policy`，该命令未执行；最终成功采样使用用户明确开启的自有热点。

首次手机低速预检因发射程序冷启动晚于录制窗，只录到13组，不作为硬件丢包结论。已改为先启动发射进程、等待控制端收到inventory，再打开录制窗并下发任务；重测保持原门槛，获得上表102组通过结果。后续复用应保留这一顺序。

结束时已核验：路由器恢复原2022驱动，两频段正常、monitor为0，两个临时无线配置键回到原值0，采集／看门狗退出；笔记本四项驱动原值恢复、回到校园网，临时测试规则撤销且发射／恢复进程退出。恢复请求曾在外层SSH等待期内超时，未重跑恢复负载，之后重新打开一次临时入口，直接读取恢复回执及实际属性完成核验；临时入口和两个内存密码通道随后关闭。台式机校园网与原热点已恢复，控制端端口已关闭。未写入启动配置、刷写整机固件或重启设备，FPGA／HDMI及旧DATA工作未恢复。

## 10月20日笔记本与路由器联测

优先继续复用现有笔记本发射，无需据本轮结果购买额外发射主机。实际路径为：蛟龙16pro／MT7922普通Wi-Fi客户端 → 台式机热点`c`；RT-AC86U在同信道旁路接收，LAN连台式机管理。通过SSH读取驱动真实枚举后，将`CurrPhyMode`从0（ax）临时改为2（n），`BWSelection24G`从0（Auto）临时改为1（20 MHz）；实际协商为2.4 GHz、信道6、802.11n。完整原始台账、PCAP和恢复状态见[本轮汇总](evidence/mt7922-tx-20261020-r3/run-summary.json)。

| 检查 | 实际结果 |
| --- | --- |
| 300 Hz／10秒发射 | 3,000／3,000个槽位成功发送，台式机收到3,000个不同槽位，无漏槽、无重复投递；发送间隔p50为3.3333 ms，最大3.6014 ms |
| 300 Hz／20秒发射 | 6,000／6,000个槽位成功发送且全部投递；发送间隔p50为3.3333 ms、p99为3.3877 ms、最大3.9571 ms；send调用最长0.2302 ms |
| 10秒发射对应接收窗 | 16.039689秒捕获8,748条CSI记录，内核丢包0；严格分组得到2,904个完整身份组，重复core记录36、缺链组0 |
| 20秒发射对应接收窗 | 26.049919秒捕获17,196条CSI记录，内核丢包0；严格分组得到5,663个完整身份组，重复core记录207、缺链组0 |
| 适配层数据 | 导出[单节点原始事件NPZ](evidence/mt7922-tx-20261020-r3/node-events/node-events.npz)，形状`[5732,3,64]`；保留69个重复身份事件及逐链到达时间，`model_ready=false` |

这证明了**本轮20秒内的300 Hz发送调度、IP投递以及真实三链接收能力**。发送完成不是独立RF帧证明，内核丢包0也不是空口无损证明；CSI中仍有背景流量和重复身份，尚未把每个UDP槽位对应到唯一无线训练字段。不能把17,196除以三当作独立样本数，也不能由5,732与6,000的差值计算空口丢包。原始CSI时间仍是接收端OS到达时间；全接收窗事件间隔p99为39.75 ms，不能称为均匀3.333 ms采样。下一步应先区分背景帧、聚合／重传和身份字段，再评估实时窗口。

初次程序使用`Thread.Sleep`时，300 Hz／10秒只发出873包、跳过2,127个槽位，全部成功投递；该失败保留在[首轮记录](evidence/mt7922-tx-20261020-r1/run-summary.json)。改用显式高分辨率waitable timer后通过上述实机检查，不将初次调度失败归因于网卡硬件。[微软说明](https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod)指出Windows 11可能降低被遮挡／最小化GUI的定时分辨率；这是与现象相符的机制，未单独证实为该机唯一原因。工具为[有界发射程序](host/LaptopTx.cs)、[临时控制与投递台账](host/laptop_tx_control.py)、[只读笔记本预检](host/laptop_preflight.ps1)及[临时LAN侧SSH放行工具](host/LaptopSshAccess.cs)。无需安装Python到笔记本。

结束时已核验路由器两频段原运行固件恢复、monitor为0、看门狗退出；笔记本两项驱动原值0／0已写回，独立的网卡重启工作进程完成，最终现场协商制式因SSH入口关闭未重新读到。台式机控制端和本机密码进程已关闭。自动审批拒绝了自动关闭笔记本SSH服务与临时窗口的命令，已请用户手动完成；确认状态以本轮汇总为准。用户自行修改的台式机LAN地址保持。

本轮未改原`[3,3,30,20]` RAW、`[1,180,60]` tokens、模型结构／数学、SDK、NPU分配或板端帧协议，未进行模型推理。一台路由器仍只代表一个独立接收节点；未复制节点、补造样本或改变30子载波预处理。FPGA／HDMI及旧DATA任务均未恢复。

## 10月19日手机配合采样（历史）

**已验证接近 300 Hz 的受控发包和真实完整三链数据，尚未验收稳定 300 Hz 独立 CSI。** 用户手机接入后完成五份实采；最终采用手机 `c_iPhone` 个人热点（最大兼容性）＋本机普通 Wi-Fi 客户端＋RT-AC86U 旁路接收。本轮原始 PCAP、逐包 CSV、失败和恢复记录见[最新汇总](evidence/controlled-300hz-20261019-r2/run-summary.json)；此前无客户端尝试保留为[前轮记录](evidence/controlled-300hz-20261019-r1/run-summary.json)。

| 检查 | 实际结果 |
| --- | --- |
| 本机热点发射 | 手机连接后能收到 CSI，但 UDP send 最长阻塞 1,480.96 ms；10 秒实际 2,345 次发送，不能作为稳定 300 Hz 来源 |
| 手机热点／本机客户端 | 最终 10 秒发送 2,999／3,000 个计划槽位，299.90 Hz；不追赶补发。临时进程优先级／定时器与末段 500 µs 忙等后，中位发送间隔 3.3334 ms，最大 7.4644 ms；丢过 1 个发送槽位，退出码 7 如实保留 |
| 最终真实 CSI | 2.4 GHz 信道 6／20 MHz、stream 0、core 0／1／2；16.039942 秒 12,606 包，各 core 4,202 包，内核丢包 0。完整连续三链事件 4,202 个，但含背景帧和重复身份 |
| 严格身份验证 | 保持原解析规则，结果仍为 false：未完整组 0，重复 core 身份记录 2,358。不能把全部 CSI 包除以三后认定为独立 RF 样本，也不能据内核丢包 0 推导空口无丢失 |
| 工程衔接准备 | 单节点事件导出为 `[4202,3,64]`：保留 packed uint32、未标定 complex128、各链到达时间、序号及重复标记；不丢弃重复、补链、重采样或生成模型协议。新增 4 项导出检查通过 |

本轮优先复用现有设备时，手机热点＋本机客户端路线的发送稳定性明显更好，暂不据此启动新主机采购。下一步需建立发包→无线帧→CSI 的逐帧对应，区分背景流量、重传、聚合和身份字段歧义；当前 BCM4366 头部 fc 是占位 0，没有 QoS TID／retry／TSF 证据，PCAP 时间是到达时间，不能宣称均匀 3.333 ms 的物理采样。

工具为 [定速发包与逐包台账](host/paced_udp.py)、[单节点事件导出](host/node_capture_events.py)、[路由器 UDP 台账](router/udp_stimulus_sink.c)及 [Windows 热点状态／临时启停](host/hotspot_control.ps1)。[实际单节点 NPZ](evidence/controlled-300hz-20261019-r2/node-events/node-events.npz)及[说明与全时段时序统计](evidence/controlled-300hz-20261019-r2/node-events/summary.json)只供适配层开发；保留完整原生字序并标记被 PHY 状态占用的字，不直接挑选 30 点。热点控制使用本机现有 `SZU_WLAN` 配置，不读取或保存热点密码。

原 `[3,3,30,20]` RAW、`[1,180,60]` tokens、模型、预处理与协议均保持。尚未实现物理 30 子载波映射、增益标定或实时模型输入；一台路由器仅提供一个接收节点，不复制成三个。结束时原驱动、两频段 ASUS／WPA2-PSK、校园网和原热点恢复，采集／认证／看门狗进程关闭，无后台续测；FPGA／HDMI、旧 DATA 保持暂停。

## 蛟龙16pro身份与筛选依据

2026-10-19 用户截图确认内置无线网卡为 **MediaTek Wi-Fi 6E MT7922 160MHz Wireless LAN Card**，PCI 总线2／设备0／功能0；硬件ID为`PCI\VEN_14C3&DEV_7922&SUBSYS_59111A3B&REV_00`。驱动提供商MediaTek, Inc.，版本 **3.5.0.1349**，日期 **2025-09-22**，签名者Microsoft Windows Hardware Compatibility Publisher。10月20日SSH实读确认相同硬件、驱动和MAC，系统为Windows 11／10.0.26200；笔记本已带到路由器旁，已完成上方联测。此前“不在同一地点”的限制已解除。未验证原始帧注入。

[Linux Wireless 官方资料](https://wireless.docs.kernel.org/en/latest/en/users/drivers/mediatek.html)列出 MT7922 为 2T2R、2.4／5／6 GHz PCIe 网卡，Linux 5.16 起支持；这是保留现有网卡的依据，不是该机 Windows 驱动或 Linux 原始帧注入／稳定 300 Hz 已通过的证据。[mac80211 的注入能力](https://wireless.docs.kernel.org/en/latest/en/users/documentation/modes.html)也不能替代具体驱动与固件实测。

当前已优先复用Windows普通客户端完成有界发送和三链CSI接收。后续仍需解决逐帧身份关联；尚无安装Linux、重启系统或验证原始帧注入的必要结论。

## 10月19日首次部署记录

硬件身份、实际 Merlin-KoolShare 系统、原驱动备份、部署顺序、原始 PCAP、解析修正和剩余限制统一见[实机报告](evidence/device-20261019-r1/REPORT.md)。已完成单链、固定三链和短时采集检查；结束后恢复原驱动及正常无线配置、关闭采集与密码进程。本次未进行 300 Hz 受控采样或模型推理，也未配置自启动。

后续使用[本机密码输入与 SSH 通道](host/router_transport.py)和已验证工具即可继续，不需要重新编译。当前 CSI 解析器已修正 BCM4366 高字节链号布局，17 项验证通过；下方离线准备是 10 月 17 日的历史范围，其清单及原哈希不回写。

后续只读探针使用当前 `router/preflight.sh` v2，已适配实机 BusyBox；10月17日缓存包里的旧探针及脚本哈希是当时快照，不作为当前脚本的逐位一致门检。

## 2026-10-17 离线准备（历史）

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
