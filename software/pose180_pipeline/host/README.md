# 180-query PC 观察与主机验证

## 常驻演示观察端

真实 CSI 演示使用独立订阅入口；不发送输入、不回 ACK、不控制板端。沿用已安装的 Three.js 与 `demo_v1/web/scene.js`，不修改候选选择、模型坐标或拓扑。

```powershell
node software/pose180_pipeline/host/resident.mjs --board 192.168.126.49 --port 39383 --http-port 39380 --seconds 1800
node --test software/pose180_pipeline/host/test/resident.test.mjs
```

打开 `http://127.0.0.1:39380/`：拖动旋转、滚轮缩放、右键平移；可切换透视／正面／侧面／俯视及关节编号。页面只接收最新完整且有效的真实结果，初始无骨架，同一 session／sequence 不重复作为新帧；无插帧或动作修正。问题1的姿态偏置、标定和跟踪继续搁置。

接收间隔超过 750ms 提示等待、2秒提示结果过期并保留末次姿态；“PC接收后”年龄来自本机单调时钟，不表示板端端到端延迟。新结果速率与浏览器绘制 FPS 分开显示，均无严格30Hz门槛。TCP断开后自动重连；普通几秒缺窗保留连接，30秒无数据才重新连接，连接等待上限5秒。PC退出或物理断线不阻断板端CSI／推理／HDMI。

默认不归档；需要诊断环时加 `--output <不存在的新目录>`，仍由独立worker维护4×64条完整记录，主线程最多一个在写和一个待写槽，慢归档替换待写并计数。固定接收槽74544字节、一个最新姿态及最多64个时间点，不随运行时长增长。HTTP只监听本机，最多8连接；观察进程到时关闭socket／HTTP／worker。

定向测试仅使用随机localhost端口和明确模拟记录，验证任意拆包、重复过滤、过期提示、重连、无ACK、模块资源及页面操作／计数语义，不替代真实浏览器GPU和板端联合长测。

## 严格主机模拟输入与完整归档

入口使用现有 `demo_v1/data` 的对齐复数窗口；不接 CSI 实采。原 `demo_v1` 基线与网页资源保持原位复用。

```powershell
node software/pose180_pipeline/host/run.mjs --stage short --count 900 --hz 30 --data demo_v1/data/mixed --output software/pose180_pipeline/runs/new-short --pacer-python python --linger 0
node --test software/pose180_pipeline/host/test/host.test.mjs
node software/pose180_pipeline/host/test/sustained_loopback.mjs --output .local/pose180-pipeline-20261025-r1/localhost-mock-900
```

持续回环仅连接 localhost 并启动真实主机入口；默认 900 帧、30Hz，假板固定 8 个输入槽，先填满 8 个信用，再在首次完整记录归档 ACK 后注入一次 200ms 最终确认延迟。每帧全部 180 候选使用明确的 mock 数值，归档逐字节比对、核对信用与不突发追赶、退出后重新绑定端口证明资源回收。该结果只验证主机协议、缓冲及背压，不构成 NPU／DDR／HDMI 实板稳定性验证。完整主机日志和原值均保存在指定新目录，失败现场不自动删除。

运行目录须不存在，父目录须预先存在。默认结果监听 `127.0.0.1:39381`，模拟输入连接 `192.168.126.49:39382`，展示服务监听 `127.0.0.1:39380`。保留 `HOST_READY`、`runtime.json` 与旧控制器需要的 `session/stage/count/hz` 字段；兼容 `--frames`，优先使用 `--count`。可用 `--input-host`、`--input-port`、`--result-port`、`--http-port` 定向控制回环测试。

默认 `--max-inflight 8`，允许 1～64；全局信用只在完整记录已归档、校验、主机 ACK 和板端最终 8 字节确认完成后归还。默认 `--max-frame-age-ms 1000`，范围大于 0 且不超过 60000；超期停止并保存已收到原值与在途清单。增加预算不改变严格实时判定。

发送按 `epoch+i/hz` 的绝对时刻执行。epoch 在首 tick 前通过 READY/GO 建立，不能按首个晚发帧重置。默认绝对发送误差预算为 20ms（`--send-tolerance-ms`）；普通调度抖动继续跟绝对槽。如果背压使上一发送跨过下一整槽，随后按一帧间隔继续，禁止追赶突发，`strict30Hz=false`，并保留原 `planned_ns`、实际发送时间与漏槽统计。`strict30Hz` 只代表本次完整输入发包节拍；处理、端到端 33.333ms 门另列。pacer 每次只发一个 tick；主机等下一帧信用可用后，以 `NEXT <delay_ns>` 传回最短等待，由 Python 高精度等待完成。Python 下一时刻同时满足原绝对槽与最短等待，不使用 Node 多次 sleep 轮询，通知队列不会按运行时长累计。

完整结果为 `PIWFUL3/3`，固定 74544 字节：128 字节头、256 字节选中姿态、43200 字节预处理输入、720 字节分数、30240 字节全部姿态。头 offset116 为 candidate_count=180，offset120 为 best_index，offset124 为 0。选中姿态仍为 `PIWPOSE1/1`，候选索引允许 0～179。

`actual.full` 在`HOST_READY`及输入准入前按目标帧数完整预写并`fsync`，使用一个至多1MiB暂存块；不只扩展逻辑EOF。本机D盘是机械盘，后续运行用`--output`指定C盘NVMe上的新目录，例如`C:/Users/cenyongdong/FPGACompetitionRuns/pose180-pipeline-20261025-r2/host-hdmi`，父目录须已存在。这样将文件分配移出逐帧路径，并分开来源读取与归档写入；不保证存储永远没有长尾。[本轮实测与存储修正](../RESULTS.md)

每条完整原值先等文件写入回调与必要 drain，再解码和 ACK。该确认表示操作系统文件写入完成，不表示逐帧 fsync。非法／非有限原值保留，不能用晚值替换。收到板端最终确认后，写 `received.jsonl` 并归还信用；`sent.jsonl` 同样逐条等待有界写入。三个写入通道各自最多一个应用层在途写，不向 Node stream 连续堆积。`--hdmi 0|1`明确本次实际模式，默认1；初始化连接等待60秒，发包后的1秒帧龄门保持。

固定内存包括 128 窗预读环（短批次相应缩小）、2 个输入封包槽、1 个完整结果槽、1 个 ACK 与 1 个最终确认槽。封包槽必须等 socket 写入回调及必要 drain 后才能复用；结果槽必须等完整归档／ACK处理结束后才能进入下条记录。网页只保留最新姿态，慢 WebSocket 的发送缓存超过 64KiB 时断开。

结束时按实际写入字节截断预分配文件，生成 `summary.json` 和 `host-delivery.jsonl`。未确认的完整原值仍在 `actual.full`；不足完整记录的尾部保存在 `actual.partial`，不足最终确认字的尾部保存在 `confirmation.partial`。失败不会自动重试 SDK 或设备。
