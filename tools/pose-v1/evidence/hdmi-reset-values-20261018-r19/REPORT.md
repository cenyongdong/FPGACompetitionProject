# r19 单次补充取证结果

2026-10-18，Windows D:/FPGACompetitionProject → SSH Lite；同r9 BOOT a0fe608b…61fb00，不重编FPGA。已批准上限为1次候选＋条件PL按键1次＋原BOOT回退1次；实际1／0／1，Open实际1次，包已关闭、剩余额度全部0。未做DMA、推理、HDMI START或长期验证，旧DATA暂停、FAT不修。

候选boot_id=079f5ab1-0699-41ad-962a-8d87f6db47fb，SSH恢复27.312秒；随后先完整恢复原BOOT文件再执行SDK先加载、首次CSR后访问的分段观察。四段均健康：

| 阶段 | CSR代次 | 观察周期＠200MHz | 毫秒 |
|---|---:|---:|---:|
| 库加载后、Open前 | 2 | 4,874,567 | 24.372835 |
| 一次Open | 4 | 5,320,896 | 26.604480 |
| Open后空闲 | 6 | 5,039,487 | 25.197435 |
| 关闭／卸载 | 8 | 1,346,337 | 6.731685 |

各段flags=0x19，窗口内复位计数0，六路AR／R握手与RVALID计数均0。一次Open、公共版本身份验证和关闭完成，SDK错误日志为空、设备无占用。本次未复现同类前置故障，因此按批准范围没有按PL_KEY2；新增的纯CSR ELF已随包部署但未执行，不能记为按键后实测通过。

原BOOT回退27.062秒，boot_id=7f8b91bf-7651-449d-aaa3-80eee79fc28e；运行与启动文件均恢复，六SDK／九启动文件符合、FPGA operating、owner为空，串口关闭且TX=0。[最终审计](final-audit.json)、[包使用次数](fallback-result.json)。

结论：SDK先加载也可以健康启动，不能把加载顺序当作确定故障原因；这也不排除顺序改变故障概率。本次不改变r18显式Open前故障原值，D45仍未修复，尚无有效的按键复位前后对照。继续只在故障后按键会受复现概率限制；下阶段可先在无SDK、无负载时，将CSR代次推进到2，再检验一次按键能否清零，独立验证复位通路。健康状态按键并非本包范围，未自行执行。

前置、参数、停止条件和执行位置见[PLAN.md](PLAN.md)、deploy/config.json；实际原值见[software-1.json](software-1.json)、[continuation.json](continuation.json)、evidence-candidate-1.tar及evidence-final.tar，完整SSH／串口／执行日志同目录。原值独立复核后更新本报告，没有重试失败SDK或销毁正常运行进程。
