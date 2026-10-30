# r51：静态底图准备与归档确认重叠

2026-10-24。在r47原生RGB565上仅拆分静态底图准备：原主线程推理后入队，先复制与模型输出无关的静态背景，同时原publisher等待PC归档ACK；收到原门检交接后才处理scores/poses、绘制动态内容、SDK写帧及等待采纳。不新增线程或SDK并发，不改变模型、SDK、数学、NPU分配、原值先保存/比较、帧协议或200ms采纳门限。r47主程序保留，新主程序独立放在native_rgb565_r51/joint。

## 实际验证

复用原r45公共对象检查点，仅编译受影响软件，AArch64 GCC9.4 Release/-ffp-contract=off下CPU回归程序和联合主程序均原生编译通过，未重新构建FPGA。FPAI构建后已停止。

板端仅普通内存CPU运行：9项回归通过，三份Result与先前r47实板保存的RGB565完整字节逐一相等，另六份NoInput/Stopped状态图两API字节/metadata一致；拥有值移动及非法输入拒绝通过。模型数组、骨架/关节标注比例及全部像素保持。原生exit0、0.189秒，运行身份仍为原BOOT的ef19aa67-8848-40c6-b4a2-df9da7e4be68。SDK/MMIO/BOOT写入/重启均0。

本次9项计时中静态准备平均4.140ms、最大5.454ms；门检后动态绘制平均0.214ms、最大0.358ms。静态工作只是移入可重叠区，并未消失；采样/冷热和r47计时不同，不能把0.214ms宣称为整幅总渲染时间。旧render API在同批对照平均4.285ms。没有HDMI实屏或AI长期验证。

联合软件包SHA256为056a5a49f80687b0ab0b4fdacb444483fe311a431f462c57728e534e7851d0ef；二进制SHA256为59bab81d6a3b07e2a2950640d1eee6d08434c0ed579ca1b9df0a729158b04ede。新候选准备结合[r50实测](../hdmi-ack-transport-20261024-r50/RESULTS.md)的已有Git OpenSSH转发；尚不能据CPU/网络各自通过断言整机达到30Hz。

已准备Git转发主机控制器。拟新增r52单次验证：最多1候选启动+1 SDK、30Hz/52800帧、2100秒硬上限及1次原BOOT回退；相同位流与AI四路，使用本次已编译软件。主机实际节拍器先预检，候选启动后恢复原BOOT文件、完成启动准入，再启动Git数据隧道与唯一SDK；错误即停、不自动重试，20ms发送节拍和200ms采纳门限不变。当前只有软件/CPU/网络准备完成，未获得或消耗该新启动/SDK权限，须明确确认后才执行。

原始构建见[build-execution.json](build-execution.json)、[build-result.json](build-result.json)，实测见[cpu.stdout.log](cpu.stdout.log)、[cpu-execution.json](cpu-execution.json)。最初Docker沙箱管道拒绝及Python命令转义解析失败原值保留，前者未开始编译，后者未执行CPU程序；随后只修正工具执行上下文/包装转义，未重跑已有有效综合/实现或改变实际结果。
