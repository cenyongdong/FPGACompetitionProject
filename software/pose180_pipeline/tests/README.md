# 离线测试位置

- `native/`：原生后处理、缓冲、显示、日志与资源安全检查；由上级 CMake 构建。
- `native/nexmon/`：实时解码／组窗检查，由 `tools/nexmon/board/CMakeLists.txt` 构建，共享 `src/input/nexmon/`。
- `sdk_stub/`：仅供 HDMI 资源测试使用的 SDK 替身，不进入正式目标。
- Python 输入与生命周期检查在 [../control/](../control/README.md) 的 `test_*.py`；PC 检查在 `../host/test/`。

本地检查不等于实板、实屏或长时稳定性验收；实际范围见 [审查记录](../resident/FINAL-REVIEW.md)。
