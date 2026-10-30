# r50：普通网络归档确认耗时对照

2026-10-24。未调用SDK、MMIO、模型或HDMI；BOOT写入、重启均0。两种已有SSH分别进行64轮合成数据交换：60784字节固定合成数据→PC本地文件写入成功→8字节ACK→8字节确认，应用两端均TCP_NODELAY，以不超过30Hz发送，不补发追赶。只有环回地址监听，通过相同反向转发连接，密码沿用内存认证且主机密钥固定。

| 传输 | 完成 | 板端等ACK平均/最大 | PC写入平均/最大 |
|---|---:|---:|---:|
| Windows OpenSSH 9.5p1 | 64/64 | 26.788 / 63.690ms | 0.259 / 1.963ms |
| Git OpenSSH 9.7p1 | 64/64 | 3.286 / 8.622ms | 0.232 / 1.131ms |

两端所有原生退出均0、序号/合成字节正确，主机服务和隧道已关闭。板端运行身份始终为原BOOT的ef19aa67-8848-40c6-b4a2-df9da7e4be68。网络确认等待的差异在无推理/HDMI时仍可复现，支持把现有数据转发复用回Git OpenSSH作为下一候选；不能把该合成对照写成AI/HDMI达到30Hz或长期稳定通过，也不能据此精确归因到SSH内部某个实现细节。

原始板端时间：[client-evidence.tar.gz](client-evidence.tar.gz)，SHA256=4b6343ceee18355194a8fa91aea617e5286588dd2da66101b76d182a21562a88；包含两次完整64轮时间与原生结果。主机原始时间及结果分别在[windows-host](windows-host/result.json)、[git-host](git-host/result.json)，执行版本见[host-comparison.json](host-comparison.json)。合成数据可由脚本确定性再生，不将生成字节冒充推理原值。
