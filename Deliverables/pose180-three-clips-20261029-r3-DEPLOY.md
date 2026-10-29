# 部署与演示步骤

适用：ARM64 Lite、板端既有 Icraft/customop 3.39.0、当前合格 `probe-free-drain-filter-v1` BOOT。板端需要 Python 3；PC 可选，需要 Node.js 20 或以上。原 epoch99 模型，TopK=3、严格 score > 0.2、CPU 多人跟踪／滤波。

## 解压到独立目录

先将 `pose180-three-clips-20261029-r3-final.tar.gz` 复制到开发板 `/tmp/`。以 root 执行以下解压命令；若目标目录已经存在，先选择另一个独立目录，避免覆盖已有运行记录。

```sh
tar -xzf /tmp/pose180-three-clips-20261029-r3-final.tar.gz -C /root
cd /root/pose180-three-clips-20261029-r3
```

推荐部署位置为 `/root/pose180-three-clips-20261029-r3`；也可整体解压到其它可写位置，脚本按自身目录定位。模型在 `board/models/`，运行记录在 `board/runs/`。官方输入在 `/root/pose180-three-clips-20261029-r3/board/dataset.piwcsi2`，来源及校验信息在同目录 `dataset.json`。主机已完成原始 CSI 格式转换，板端仍执行预处理与新推理，不需要安装 NumPy／h5py。

## 启动前

若旧包仍在运行，先使用旧包的停止入口，并确认原生进程、监督进程及设备占用结束且关闭证明成立。本包 `stop.sh` 只管理本包，不能用来结束其它目录的旧任务。

本硬件每次 FPGA 配置只能消费一次功能启动入口。已使用过、或首次 `check.sh` 报未知 boot_id 时，在旧任务安全结束后执行下列只读 BOOT 核对，再安排正常重启：

```sh
sh prepare-boot.sh
# 仅当 prepared=true，且已有任务安全结束后：
reboot
```

重连后回到本包目录再执行所选输入的 check。`prepare-boot.sh` 只核对启动文件并保存下一次启动凭据，不写 BOOT、不自行重启。核对失败或仍有占用时先处理原因；包内 `boot/BOOT.BIN` 仅作备份。

## 选择一次演示

官方预采数据：

```sh
sh check.sh --input-source official_dataset
sh start-dataset.sh
sh status.sh
```

一次启动，按以下顺序在同一 SDK 进程内播放，片段之间不重启开发板；每段切换重置跟踪状态。

| 顺序 | 人数 | 官方来源 | 样本范围 | 展示时长 |
|---|---|---|---|---|
| 1 | 1 | train / S51_10 | 10–159 | 10.0 秒 |
| 2 | 2 | train / S52_16 | 97–231 | 9.0 秒 |
| 3 | 3 | train / S23_43 | 94–228 | 9.0 秒 |

每段 15 Hz 播放时长为演示时间线，不作为原始采集时长。片段边界有约 0.1 秒收尾间隔。

默认一轮，EOF 正常退出；需要更长展示时，在首次启动前选择 `sh start-dataset.sh --dataset-repetitions 3`。训练片段演示不计独立测试精度。

实时采集：

```sh
sh check.sh --input-source live_csi
sh start-live.sh
sh status.sh
```

实时入口复用已安装的路由器采集服务；默认处理期为 0 秒（0 表示持续到手动停止），也可在首次启动时指定 `--seconds 300`。`start.sh` 的默认输入为 `official_dataset`。

## 结束、切换与 PC

`sh stop.sh` 请求正常停止；随后用 `sh status.sh` 核对 `running=false`、`native_shutdown_complete=true`、`device_owners=[]` 和 `network_cleanup_pending=false`。数据集 EOF 后同样核对。本包清单内的片段自动顺序切换，无需中途停止或重启。整轮结束后再次启动程序，或切换到实时输入，仍须重新准备 BOOT 凭据、正常重启并 check。若为 `release_blocked` 或缺少完成证明，保留原资源与独占，按 STARTUP-GUIDE.md 处理，不强杀或重试。

PC 解压同一个包，在 Windows 包根目录执行 `./start-pc.ps1`，浏览器打开 `http://127.0.0.1:39380/`。默认板端地址 `192.168.50.49`；可用 `./start-pc.ps1 -Board <实际可达地址>` 指定。关闭 PC 服务不停止板端推理和 HDMI。

初次打包阶段只做本地构建、mock／接口替身与 PC 验证；后续已读取相同 r3 板端内容的既有 420 帧双路输出与正常关闭记录。最终 PC 修订通过 22 项本地检查，最终压缩包没有重新启动一轮实板测试。当前结论见[项目进度](../PROJECT-PROGRESS.md)，不扩大为长期或精度验收。

本文是项目侧更新的部署说明；压缩包内 Markdown 保持交付时快照，未因本次文档整理重新打包。

## PC 有线连接（2026-10-29 修订）

启动器自动查找已有 Node.js 20+；无需 npm install。当前开发电脑的有线地址为 `192.168.126.100/24`，板端固定地址为 `192.168.126.49`：

```powershell
.\start-pc.ps1 -Board 192.168.126.49 -LocalAddress 192.168.126.100
```

其它电脑将 `-LocalAddress` 改为本机实际有线地址。先启动 PC 服务并打开 `http://127.0.0.1:39380/`，再开始板端演示。终端 `PC_BOARD_WAIT` 记录连接失败原因，`PC_FIRST_RESULT` 表示已接收真实新结果。仅重启 PC 服务不需要重启开发板。默认 `192.168.50.49` 为演示期间临时别名。
