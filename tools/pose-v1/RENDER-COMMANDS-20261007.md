# 渲染与只读视频核对命令

已执行完成，见[结果](RENDER-RESULTS-20261007.md)。以下是保存的接口，r1路径/目录不可重跑或覆盖；有新修改时用新修订、新包/构建与门禁。

## 构建与复核

Windows项目根目录，使用既有Conda和FPAI，无新依赖。

```powershell
& .\tools\pose-v1\Build-Render.ps1 -Package PACKAGE -BuildTag mixed-NEW-REVISION
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\render_gate.py review-build --package PACKAGE --build BUILD --output EVIDENCE/build.acceptance.json
```

PACKAGE/BUILD/EVIDENCE/NEW-REVISION为新修订占位；包manifest需先固定全部source/build_files/hash与输入来源，`render_gate.py freeze`只完成已准备包的runner/hash冻结，不自动生成任意新修订的初始包。
产物：pose_application_render_check.arm64、pose_skeleton_render_check.arm64、pose_video_capability_probe.arm64及SDK/源码审计。

## Lite分阶段

传包、三个程序、build-result和同包新build门禁至新work/gates；chmod程序。登录shell不直接set -eu，每阶段完整回传核验后传回对应gate再推进。

```sh
sh package/run-render-validation.sh cpu-render
sh package/run-render-validation.sh host-check
sh package/run-render-validation.sh net-render-three
```

CPU阶段自检＋27份既有结果渲染，每个调用限120秒，不执行SDK；Host107限300秒；网络接入整体限300秒，三帧新前向在返回后绘图，不初始化HDMI/VPU。
网络任务以受控后台作业运行，持续检查results/listener.json（就绪等待上限90秒），确认READY后立即发送三份原始CSI：

```powershell
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\send_application_cases.py --package PACKAGE --host 192.168.126.49 --cases three --fps 2 --output EVIDENCE/net-render-three.sender.json
```

发送方不做预处理、预测或读GT。超时、SDK/总线错误、身份/输出不一致停止保存，不自动重跑、改BOOT或降低门检。

```powershell
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\render_gate.py review-stage --stage STAGE --package PACKAGE --build BUILD --results RETURNED --output EVIDENCE/STAGE.acceptance.json
```

STAGE为cpu-render/host-check/net-render-three。核对完整清单、程序/源/SDK/前门禁、退出/内核、107例、1173融合/每帧745及完整输入/输出；绘图选择、原坐标、投影和三格式独立NumPy核验。生成审查catalog在回传根目录之外，不修改原始回传清单。

PNG预览导出使用`review_skeleton_render.py --results RETURNED/results --input RETURNED/results --catalog REVIEW-CATALOG --output NEW-REVIEW --preview NEW-PREVIEW`；只编码原RGB，不改图像或姿态。

## 视频查询

```sh
timeout --signal=TERM --kill-after=2s 15s ./pose_video_capability_probe /dev/video0
python3 video_readonly_audit.py NEW-OUTPUT.json
```

probe只允许QUERYCAP/ENUM_FMT/ENUM_FRAMESIZES与open/close；不要把它换成编码/相机示例。保存stdout/stderr/exit及dmesg前后，核对MPLANE能力与配套表。查询通过不作编码、HDMI或RTSP通过。
