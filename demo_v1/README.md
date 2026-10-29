# demo_v1：论文CSI → Lite融合推理 → 主机实时3D

**版本定位（2026-10-29）：** 本页保留早期工程、兼容接口或对应批次结果，文中的“当前”只指该版本。现行 180-query 主链在[主工程](../software/pose180_pipeline/README.md)，运行及验收范围见[最终进度](../PROJECT-PROGRESS.md)；旧命令不作为最新部署入口。

本目录保存独立demo，BOOT、共享FP16模型、SDK、CPU数学、Gather注册和NPU分配保持。HDMI、VPU和RTSP不在本程序链接或启动范围内。

## 数据和模块

| 目录 | 职责 |
|---|---|
| `shared_fp16/` | 从已完成独立30分钟验证的共享实现导入的必要源码；对应身份见`shared-source.json`，原数学与SDK桥不改 |
| `diagnostics/` | 可选op192有界读回观测覆盖层；默认不启用，保持原读回／wait与数学，详见该目录说明 |
| `board/` | `[3,3,20,30]`复数接口、轴转置、有界队列、单Engine编排、保存及发布 |
| `output/` | 沿用PIWPOSE1的SDK无关拥有值与编码 |
| `host/` | MAT整理、提前读取128窗、30Hz绝对节拍、完整结果接收及独立数值复核 |
| `web/` | Three.js实时14关节渲染；坐标不平滑、不逐帧居中 |
| `tools/` | 现有FPAI构建、SSH内存认证、板端只读身份检查及资源观察 |
| `tests/` | 原CSI/预处理逐位、非法输入、队列、分包及节拍检查 |

输入为原始complex128，形状依次为接收节点/天线/时间点/子载波。主机不执行预处理或模型、不读取GT；板端只交换时间和子载波轴，继续调用原预处理生成`[1,180,60]`。

`data/full`是全部7,824窗论文测试集。`data/mixed`另从89,946窗训练数据的215个序列均衡选择7,824窗，按完整来源片段与测试片段交替排列，保留原序列内部次序。训练、测试标记随输入清单、接收日志和画面保留。训练样本不作为独立泛化精度证据。

板端每进程唯一Engine，主线程串行推理。输入队列8帧，结果队列64帧；满载向生产者施加最多1秒的背压，超期或首次错误唤醒并停止，不覆盖旧帧。v2由输出线程将全部实际input/scores/poses保存到主机`actual.full`，等待写入回执，再作有限性/参考门检并确认可展示；推理线程不直接访问磁盘或网络，仅在队列满时等待。异常时当前和所有尚未确认的拥有值另存板端`unpublished-*.f32`，原SDK异常取证保留。网络错误、SDK异常或数值失败停止受影响负载，不自动重连、重发或重建Engine。早期v1的板端`actual.f32`和原失败原样保留。

## 协议与计量

输入PIWCSI2/v2：小端`<8sIIQQ>`头，magic为`PIWCSI2\0`、版本2、86400字节负载、帧号、主机单调时间ns。负载为R/A/T/N顺序，每个复数用real/imag两个float64，共86432字节。旧PIWCSI1/v1不改变。

完整结果PIWFUL2/v2原值记录共60784字节：128字节头、原PIWPOSE1的256字节骨架、10800+100+4200个FP32实际输入/分数/姿态。主机先保存完整字节，再检查顺序、有限性及最高分候选和完整数组的一致性，回传小端u64传输序号作为保存回执；板端门检通过后返回相同u64作为展示确认。主机收到确认后才发布WebSocket。原始记录文件不包含这两个控制序号，保留无改写的全部模型输出。v1归档仍可离线读取。帧号、来源时间、调用号和传输序号贯穿两次确认。

主机CSI入口直连Lite TCP39382；结果通过已核验主机密钥的SSH反向转发到主机loopback TCP39381。HTTP39380与WebSocket仅监听主机127.0.0.1。浏览器地址为`http://127.0.0.1:39380/`，没有归档自动回放或参考值替换。

CSI发送和结果接收都由同一个Node进程以`hrtime.bigint`打点。Python3.14高分辨率等待只发节拍通知，自己的时间值不参与端到端相减，也不修改系统定时器或电源配置。提前读取128窗约11MB；计时前预分配完整输出文件，结束后裁至实际字节数。本轮Node与节拍子进程使用AboveNormal调度优先级，随进程退出回收。渲染FPS、真实推理率、队列等待、端到端延迟和33.33ms超期分别统计。

阶段计时采用sidecar，不修改协议：板端`delivery-timing.jsonl`保存末256条编码／发送／等待ACK／确认时间及有界入队耗时，`delivery-summary.json`保存整轮最大值；主机`host-delivery.jsonl`保存整轮接收、文件写入、解码、ACK与展示确认时间。文件写入回调完成后才ACK，未承诺逐帧fsync。可用`tools/analyze_delivery.py RUN --board-results RESULTS`复核。仅short允许`--archive-delay-ms 400 --archive-delay-every 300`注入保存停顿；长期默认关闭。

已有三窗冻结参考继续按ADR_48 v2检查：输入/全部分数逐位，全部候选有限，参考score>0.2的候选最大关节欧氏差≤3mm。其它样本完整保存并检查形状、有限性、身份和选择，不宣称已有全数据集冻结精度结论。

## 运行入口

运行产物位于忽略Git的`build/`、`data/`、`runs/`。已使用目录保留；后续运行使用新目录，不覆盖失败证据。现有Python环境：`C:/Users/cenyongdong/miniconda3/envs/torch_gpu/python.exe`提供NumPy/h5py，默认Python3.14提供节拍/SSH工具；Three.js/ws只读复用`software/pc_viewer/node_modules`，不安装新版本。

```powershell
# 已有FPAI运行时，编译并生成新包；不运行板端负载。
python demo_v1/tools/build.py --tag NEW

# 启动主机接收、绝对时隙发送和3D服务，等待板端连接。
node demo_v1/host/run.mjs --stage stress --data demo_v1/data/mixed --output demo_v1/runs/NEW

# SSH只从隐藏的交互输入取得密码，主机密钥固定校验。
# SESSION取自该主机运行的runtime.json；安装应先核对package.tar身份。
# --run-name必须新建，不能复用既有成功或失败目录。
python demo_v1/tools/ssh.py ssh 'cd /root/demo-v1-20261022-r1/r2 && python3 board_guard.py --stage stress --run-name NEW --session SESSION' --reverse --timeout 0

# 完成后独立复核主机保存的完整输出。
& 'C:/Users/cenyongdong/miniconda3/envs/torch_gpu/python.exe' demo_v1/host/analyze.py demo_v1/runs/NEW
```

当前SSH工具的SCP允许目录限定为本轮`/root/demo-v1-20261022-r1/`；新的部署目录须按明确任务修改允许范围。阶段为basic=3窗/5Hz、short=900窗/30Hz、medium=9000窗/30Hz、stress=54000窗/30Hz。板端包装器拒绝覆盖同名阶段，不自行赋予失败负载重跑或BOOT操作许可。`--timeout 0`仅表示保持SSH监测，防止外层等待销毁正常执行的30分钟负载；实际负载仍有明确帧数，通信异常有界停止。

本轮实测与当前恢复入口见`RESULTS.md`，不以构建成功、渲染FPS或历史结果替代30Hz验收。
