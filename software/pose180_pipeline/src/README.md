# 当前核心源码

正式运行目标是 `pose180_demo`。相关头文件与实现按模块放在一起；从 [app/main.cpp](app/main.cpp) 进入，再沿下表阅读。目录调整不改变模型、数值处理、设备完成契约或帧协议。

| 目录 | 主要文件 | 职责与边界 |
|---|---|---|
| `app/` | [main.cpp](app/main.cpp)、[option_value.hpp](app/option_value.hpp) | 参数解析、输入选择、唯一推理线程和全生命周期；`strict_main.cpp` 保留早期严格归档入口 |
| `common/` | [core.hpp](common/core.hpp)、`types.hpp`、`wire.hpp` | 拥有值、最新窗口、固定缓冲及协议；不持有设备资源 |
| `input/` | [csi.cpp](input/csi.cpp)、[dataset.cpp](input/dataset.cpp) | 实时采集和官方预采 CSI 两个互斥入口，都发布同一种拥有值 `Input` |
| `input/nexmon/` | `pcap_stream.*`、`adaptive_ingress.*`、`ingress.*` | 实时 CSI 解码、三 RX 组窗与重连；工具程序也链接这里 |
| `preprocess/` | [preprocess.cpp](preprocess/preprocess.cpp) | 原复数 CSI → `[1,180,60]` FP32 数学；保持原计算顺序 |
| `inference/` | [runtime.cpp](inference/runtime.cpp)、[release_guard.hpp](inference/release_guard.hpp) | 唯一 SDK 所有者、原 epoch99 推理、首次输出读取、在途释放保护 |
| `pose/` | [postprocess.cpp](pose/postprocess.cpp)、[single_person.cpp](pose/single_person.cpp) | 候选筛选、人物关联和 CPU 单人连续性滤波；原始结果与展示结果分开 |
| `display/` | [hdmi_renderer.cpp](display/hdmi_renderer.cpp)、[hdmi_output.cpp](display/hdmi_output.cpp) | 几何投影、RGB565、HDMI 采纳／STOP／资源释放与待机画面 |
| `io/` | [io.cpp](io/io.cpp) | TCP 输入、独立结果／状态／PC 消费者；PC 断开不控制推理生命周期 |
| `diagnostics/` | [journal.cpp](diagnostics/journal.cpp) | 有界异步日志与状态输出 |
| `compat/` | `network.hpp`、`r9_startup_observer.hpp` 等 | 严格链及旧硬件配置的兼容声明；当前合格配置不启用旧诊断 MMIO |

启动与数据准备在 [../control/](../control/README.md)，PC 服务及网页在 [../host/](../host/README.md)，测试在 [../tests/](../tests/README.md)，统一构建在 [../CMakeLists.txt](../CMakeLists.txt)。两项展示操作见 [双输入说明](../resident/DEMO-INPUTS.md)。

输入路径：`control/input_config.py` 显式选择 → `input/csi.cpp` 或 `input/dataset.cpp` → `common/core.hpp` 最新完整窗口 → `preprocess/` → `inference/` → `pose/` → `display/` 与独立 PC。官方入口读取原始 CSI 并执行推理，有限播放在 EOF 正常收尾。

本目录是当前 180-query 主链的维护位置。预处理、HDMI 底层和兼容声明从已验证历史实现原样收拢；原 `demo_v1/`、旧 `software/core/display/` 及 r47／r53 副本继续供历史工程使用。不要用新文件覆盖历史包。`pose/` 中的实验性 PL 扩展仅保留，不因此恢复开发；可选相位分支仍在 `software/core/input/`，未接入正式运行目标。
