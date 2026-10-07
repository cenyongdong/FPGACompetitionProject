# 首批生产接口与TCP验证命令

本轮由代理执行完成，见[结果](APPLICATION-RESULTS-20261007.md)。以下保存复现接口，已完成目录禁止重跑/覆盖。新修改必须准备新包和门禁；不直接运行历史失败目录。

## 本机准备与构建

执行位置为Windows项目根目录，Python为既有 `.local/pose-v1-onnx-conda/python.exe`，Docker Desktop/FPAI已安装，不新装依赖。

```powershell
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\application_gate.py prepare --package .local/pose-v1-application/package-NEW-REVISION
& .\tools\pose-v1\Build-Application.ps1 -Package .local/pose-v1-application/package-NEW-REVISION -BuildTag mixed-NEW-REVISION
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\application_gate.py review-build --package PACKAGE --build BUILD --output EVIDENCE/build.acceptance.json
```

上面的NEW-REVISION/PACKAGE/BUILD/EVIDENCE为后续新修订占位，不可原样执行。通过标准：两个ARM程序、SDK身份、包/全部构建源匹配，无编译error与RPATH/RUNPATH；失败保留停止。

实测r2包411项，构建19来源；应用 `pose_application_check.arm64`传为 `pose_application_check`，纯传输程序传为 `pose_transport_check`；同时传包、build-result.json和对应build门禁到新板端work/gates。

## 板端门检

独立 `sh`执行，登录shell不设置 `set -eu`。每阶段退出后完整回传，独立审查并把对应新门禁传回gates，才能进入下一阶段。

```sh
sh package/run-application.sh host-check
sh package/run-application.sh regression
sh package/run-application.sh net-three
```

分别为CPU/Host107（300秒、无Device::Open）、生产/验证入口原三帧＋重复（180秒、8次真实前向）、三帧TCP（原120秒整体时限）。硬件阶段runner显式传 `--allow-device-init`。
产物分别为run-host-check/run-regression/run-net-three；非0/stdout或stderr异常/身份/内核变化停止并保留，不进入下一阶段。

网络阶段由受控后台任务运行，先确认results/listener.json及READY，再立即从Windows发送。接收端默认39001，只在指定板端IP绑定；不启动常驻服务或自动重连Engine。

```powershell
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\send_application_cases.py --package PACKAGE --host 192.168.126.49 --cases three --fps 2 --output EVIDENCE/net-three.sender.json
```

27帧最终成功执行采用[外部控制脚本](run-application-controlled-network.sh)：放在work根目录，原package不增加文件；新目录 `run-net-27-controlled-r1`、总时限300秒，90秒监听检查后立即发送 `--cases 27`。它沿用同一程序/包及net-three门禁，只修正启动/等待预算；已完成该目录不能重跑。原120秒失败目录保留。

## 回传复核

```powershell
& .\.local\pose-v1-onnx-conda\python.exe tools\pose-v1\application_gate.py review-stage --stage STAGE --package PACKAGE --build BUILD --results RETURNED --output EVIDENCE/STAGE.acceptance.json
```

STAGE依次为host-check/regression/net-three/net-27。最终27阶段的RETURNED必须指向完成的controlled目录，不能指向旧失败或正在运行的部分回传。
核对完整files.sha256、程序/SDK/前门禁、exit/stderr/dmesg、1173融合/真实RAW、PS输入/全输出逐位此前板端、每帧0→745、生产调用无冻结参考、单时钟有限采样。外部脚本还须核对回传orchestration.json的脚本SHA与300秒设置。

直接API生产配置使用 `minimal_log=true`、小且有界的 `diagnostic_frames`，单Engine串行；验证入口保留冻结参考。当前有限CLI与上述回传不替代长期守护服务、整机5Hz、渲染或双路验收。
