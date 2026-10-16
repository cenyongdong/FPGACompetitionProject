# 新HDMI CDC待闭合项

执行位置为Windows隔离整机工程；本记录是r4综合报告的结构审查，不是实板故障结论，也不触发已暂停的旧DATA调查。

- 邮箱payload/response：握手期间源总线保持；请求/响应toggle两级同步。原clock false-path曾覆盖上限，r4已从实际路径确认5ns/10ns。CDC-1及CDC-15不能仅按数量放行，需要结合稳定总线协议、实际路径延迟及目的使能路径检查。r3实际实现子进程已确认相同约束生效。
- FIFO Gray与像素计数Gray：注册Gray源，目的两级ASYNC_REG；10/10/32位各有源周期max-delay及bus skew。必须查看布线后的skew及最大延迟，不把结构信息等同物理收敛。
- safe_idle和display_running经组合控制到同步器首级会被CDC-10标记。原子快照才证明内存释放；idle_csr同步诊断不用于释放。需分别检查时钟域内状态转换及目的同步消费。
- pixel_release由PLL/CSR/内存复位组合异步置位、像素域同步释放，CDC-12反映多源复位扇入；这是待审复位结构，不能把各来源独立计数直接解释成多个硅故障。
- FIFO当前wr_release/rd_release限制ready/empty，但wr/rd指针、Gray同步器和lane寄存器仍直接接收组合fifo_resetn。报告的两项CDC-7指向lane异步CLR。**尚未确定是否构成实际功能故障**；不得用全域false-path隐藏恢复/移除检查。如果实际布线显示这些新复位路径不能满足门检，拟将复位同步链与每域数据状态分为独立always块，由各域release最后一级驱动该域状态复位，并仅对真正异步复位同步器的输入作明确约束，再执行新目录core/pixel及PHY验证、综合和实现。保持原FIFO地址宽度、帧/AXI协议、模型和SDK不变。

当前impl_hdmi_r3正在运行。不得修改其正在使用的RTL/约束；先取实际报告再确定修正范围。仅原AI时钟两个Min Period检查已有用户定点例外，新HDMI时序仍必须核验。
