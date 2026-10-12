# 目录预建与首次错误/晚源对照结果

2026-10-11。程序d3772b3c82ce8a5e02a4b83c4427a4d36794bed5922a945ee0ad4bbfb22ef875。本批已结束，失败不重跑；所有测试/管理器及代理连接已关闭。

## 已完成的最小调整

新SDK无关PreparedDirectories独占新根；真实SDK部署/内存往返之后、deployment.ready之前预建4/100空目录。热路径只顺序领取一次拥有路径，无mkdir/stat/readdir，输入/identity/stages/outputs仍原位置保存后比较。新入口仅适配此模块，原152软件和上一批全部源读实现哈希保持；数学、等待/复制、物理来源、帧协议、SDK/模型/RAW/BOOT/CMA保持。Phase::Directory在新入口表示令牌领取，不混作mkdir耗时。

Native和ARM四/100目录、126拒绝/线程/所有权/保存兼容通过。原租约Guard/载荷/时隙/Trace/ioctl合同通过；ARM Host CPTR公开read八输出188160字节逐位，未物理Device/Session。旧Host107引用已验收，不伪记新跑。首次本机解包因测试符号链接停止；保留原tar/部分解包，新规则只导入普通文件字节并记录链接元数据，四非法路径/链接拒绝过，无板端重跑。tar未来mtime警告保留，不改板钟。

| 阶段 | 准备目录耗时 | 调用结果 | FP32完整正确值 | 热领取最大 |
|---|---:|---|---:|---:|
| four | 0.56224ms | 4/4、exit0 | 47040 | 0.00723ms |
| off | 12.41432ms | 100/100、exit0 | 1176000 | 0.06393ms |
| on | 11.84572ms | 前94正确，第95次inv94失配、exit1 | 1105440 | 0.08171ms |

合199次实际前向，198次完整正确/2328480FP32；第199次两输出均完整保存，其中96值错误，不把全部2340240实际输出标作通过。每次0→11，绝对5.05Hz时隙和50秒初始门禁/60秒序列/180秒外部预算保持；本批没有目录或截止失败。数据保存仍有等待：off最大52.56402ms，on输入486最大166.99851ms（线程CPU0.35076ms、自愿切换1、缺页0），未超时，不作磁盘/调度责任结论。

## 新取得的失败证据

on inv94实际A，上一inv93为B：DATA4386/7560值中96个有限值错误，全部逐位同上一B的相同偏移；INDEX4390/4200值全部正确。A/B全部7560参考DATA本来不同，排除两个参考局部相等造成的误判。

六段每段64字节，字节偏移28672、28928、29184、29440、29696、29952，间隔256；物理范围0x6816000–0x6816040…0x6816500–0x6816540。首次来源109113344/109092864、chunk/offset/capacity和dtype在四晚读中均保持，ready=true/计数11不当DDR fence。

首次CPU拥有字节FNV与错误文件绑定，该指纹在文件保存后记录。保存助手不改写拥有缓冲区，支持首次副本异常；本批没有copy返回瞬间或保存前即时指纹，不把记录时间误作早期现场，也不把文件改值当已证根因。原输出未覆盖修补，未执行inv95；预建的call95–99仍空。

首次forward427.89μs，两复制143.75/96.90μs，无该次尖峰。首次DATA复制结束约3.42335ms后，原真实Tensor租约内公开Tensor::read取得正确DATA；两轮四读全部逐位独立参考，共94080字节/23520FP32，地址及chunk身份相同、主线程/代次有效。没有额外wait/sleep/reset/forward/write/cache helper，诊断不用于继续计算。租约4/100/95开关相同，forced0，失败capture1/物理read4，Session销毁前清空。

独立19成员ZG组未运行CPU ScatterND，因此本次不能归因于ScatterND数值计算；它加强了生产完成/首次SDK读取或复制/共享暂存及缓存交接方向的证据。晚源正确仍不能证明首次DDR已完成或缓存根因。首次Host Tensor已在原循环结束释放，本批未保留它进行失败CPTR读；下一需补充这一最小边界。

## 视频、资源和清理

on实际309raw提交/308归还，308拥有packet/56763字节；307 NoInput图像ID0–306连续解码，尾307/308未解码。1844公开VPU ioctl，两端两缓冲/单编码线程；190首复制均与提交→capture跨度交叠，非硬件busy/fence证明。两abort STREAMOFF成功、workers join后租约/Session毁、prefix1→0/allSDK0；正常drain-LAST未通过。冻结VPU summary提交/归还0是异常前未返回EncodeResult的默认字段，不作实际无工作。NoInput不计新姿态吞吐。

资源只读101→101个普通512KiB单位，规整0；阶段allocstall/reclaim/OOM/compact均0，pgmajfault增3不能定位坏值。最终BOOT/SDK/模型/内核逐位同、FPGA operating、本批程序/管理器/端口清理通过，MemAvailable732908KiB/CmaFree27204KiB仅现场；无清缓存/重启/CMA/BOOT/SDK/模型改变。

## 结论与恢复

目录创建已移出热路径并经本批验证；首次错误/两轮正确晚源读终于有同一活租约物理证据。并发数值根因未修，on100未过，完整103/严格整机5Hz/30分钟/HDMI/零拷贝仍待；管理83/100保持，不以取证增加验收进度。

[ADR_44](../../ADR/ADR_44.md)／[失败](evidence/producer-prepared-20261011-r1/on.failure-review.json)／[指纹](evidence/producer-prepared-20261011-r1/on.fingerprint-review.json)／[完成](evidence/producer-prepared-20261011-r1/completion-review.json)／[下一](PRODUCER-PREPARED-NEXT-20261011.md)。
