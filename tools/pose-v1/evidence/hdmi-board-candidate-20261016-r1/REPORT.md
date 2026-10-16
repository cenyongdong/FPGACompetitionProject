# HDMI整机候选受控启动与静态实屏证据

2026-10-16：HDMI修复已完成整机接入、实际候选启动和静态实屏验证。用户现场确认“显示稳定的八条色条”；双ABI、PLL/idle/错误门检及约148.5MHz像素计数通过，OSD分辨率/刷新率尚未提供。目标仍为1920×1080@60；r5布线WNS+0.030ns/WHS+0.029ns，原两个AI Min Period例外及其余告警保留。已使用新授权的一次候选重启，SSH约53.6秒恢复；原BOOT随后完整还原并读回原SHA，其余启动文件/六SDK不变。运行中仍为候选静态色条，不是运行中已回退；下一次启动选原BOOT。未进行显示DDR DMA、帧切换/在途STOP、NPU推理或整机实时验收，旧DATA继续暂停。跨重启/tmp清理导致的恢复源丢失已通过主机原始回传及/root持久暂存解决；另查到FAT脏标志与两条合计2168簇的未引用链，来源未知，未修复，启动区停止新增写入。

## 平台、前置与授权

Windows主机D:/FPGACompetitionProject；板端root@192.168.126.49，固定SSH主机密钥、内存认证。已有Vivado2018.3＋JFM/Procise离线587文件证据封存，见../hdmi-integration-20261016-r1/files.sha256.json。本批执行位置以每份remote-code.py和execution.json为准；初始/tmp/hdmi-board-candidate-20261016-r1，重启清理后改为/root/hdmi-board-candidate-20261016-r1。

用户明确批准临时BOOT替换、一次候选启动和必要时最多一次原BOOT回退重启；见authorization.json和Agents有效授权。已使用候选启动一次，回退启动0次。没有永久替换BOOT、修改uEnv/DTB/内核/SDK/模型，旧DATA暂停。

## 实际执行与结果

1. 新板测目录只读挂载已核实FAT16 /dev/mmcblk0p1，完整备份BOOT/uEnv、九份根文件SHA及可用空间，卸载。原BOOT完整回传主机SHA通过，候选/原BOOT/探针逐项传输校验；见prepare、transfer和verify-transfer。没有猜测块设备。
2. UART COM7/115200 8N1接收先打开，DTR/RTS关闭、发送0字节；安装候选后读回全BOOT SHA、比较其它文件、sync并卸载。一次重启预检再次从原始FAT读取候选SHA并确认无相关设备owner，之后仅调用一次reboot。启动监测预算180秒，实际53.573秒观察到新boot_id ab6d59c6-4921-4733-b04b-a0c4154069ae。失败的SSH连接只是同一次正常重启期间的等待，没有追加重启。
3. UART完整42739原始字节，231.934秒后主动关闭。FSBL报告610.25ms PL下载完成，三分区Load Success、U-Boot和Starting kernel均记录，Linux登录出现。uEnv没有改变，其mmc0:2二次fatload失败原文保持，不能假设加载成功。SDK日志的板端日期重置到2026-03-13，未修改系统时钟；实际执行日期使用主机2026-10-16及boot_id。
4. 首次恢复在源文件open处发现/tmp批次消失，尚未挂载/写入，exit1原样保存。查明tmpfiles的D /tmp配置。主机原始回传SHA仍正确，新/root目录重传后核验实际候选BOOT/六SDK，restore-original-BOOT-r2还原原SHA，全部其它启动文件内容相同，sync且卸载。此后未再写启动区。失败不是恢复通过，不把候选运行状态称为已回退。
5. 静态探针以公开原SDK执行，每次远端5秒预算、SSH15秒；read-only及bars各约1.3秒exit0。版本25122301/FMSHZGV3TECH-AID - 24160628、core ABI 0x48444d01/board ABI 0x48445301通过；控制状态0x3→0x7，PLL/idle为1、适配错误为0。100ms观察计数对应像素约148.5MHz；目标148500000/742500000字段仅为声明，不冒充实际测量。没有显示帧分配、Session、DMA或推理。
6. 用户明确现场答复“显示稳定的八条色条”。静态画面实屏通过，OSD分辨率/刷新率未提供，不伪填1080p60接收参数。FPGA当前保留候选静态图案，所有探针已退出、无相关设备FD owner，串口关闭。现BOOT为原SHA，六SDK未变，下一次启动选原配置。

## 文件系统告警及停止边界

post-probe-readonly相比同次启动的pre-probe内核新增一条FAT未正常卸载告警，完整差分kernel-delta.txt保留，不称内核日志不变。只读检查两FAT相同，FAT16 entry1=0xffff、clean/no-hard-error均真，但BPB状态字节37=1。没有fsck.fat/fsck.vfat/dosfsck。

只读遍历11文件/1目录、40735987字节，未发现交叉链、环或文件簇链长度错误；但4662已分配簇中仅2494被目录引用，2168簇未引用，元数据检查exit1严格保留。离线快照分类证实无bad/reserved标记，另有1064和1104簇两条链，共35520512字节（约33.9MiB）；来源没有操作前FAT快照可证，不能归因于本批或称无害。BOOT和所有现有启动文件SHA仍与初始相同。元数据已完整保存，未安装检查器、未修复或清理孤链、未修改脏标志，启动分区保持未挂载并停止新增写入。

## 尚未验证

HP2实际DDR RGB565扫描、完整来源映射、翻帧/接受ID、欠载故障及带在途读STOP/stopped ID、帧块安全释放、骨架接入、NPU并发和整机实时性均未执行。本阶段静态成功不替代这些门检。原两项AI Min Period例外和REQP-1577/O5/MIG/SDI/AI CDC等警告保留，实屏静态成功不等于全CDC/电气眼图签核。回退重启只在必要且仍在限定授权内时使用。
