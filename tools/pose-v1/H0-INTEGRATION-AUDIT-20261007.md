# 视频与骨架接入资料核对（H0，2026-10-07）

## 工程内容总结

本轮只读本机源码/参考资料，无视频设备初始化、寄存器写入、编码、RTSP服务、安装或位流操作。
已有参考代码可用于设计接入，但**720p60与当前25122301位流的配置对应、14关节语义及视频缓冲区生命周期仍未完成核验**。
不会凭NPU模型成功自动认定视频路径可用。

### HDMI

沿用[HDMI静态核对](HDMI-STATIC-AUDIT.md)的原始源码与页码依据：参考包装器默认1920×1080 RGB565，只写显示缓冲区地址，未配置像素时钟和消隐。
参考RTL有720p参数分支及可写时序线索，但尚不能证明它们属于板上25122301。
720p60按参考1650×750总像素需要74.25MHz；当前参考Xilinx时钟配置为148.5MHz，不能只改软件宽高就认定720p60。
Lite手册和原理图建议720p或更低，首版720p60目标保持。

下一阶段需确认当前位流配套时序/像素时钟、显示缓冲区格式/行跨度/对齐及换帧边界，再制定独立测试图门检。
本轮不自行选择候选寄存器地址、不切1080p、不生成或更换BOOT。

### 14关节顺序与连接

原算法目录为`D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo`。

| 来源 | 原源码事实 | 结论边界 |
| --- | --- | --- |
| `opera/datasets/wifi_pose.py:64`及103 | 直接加载keypoint.npy转FloatTensor，keypoint_process调用被注释 | 当前数据保留标签索引顺序，不能从函数名推导关节名称/左右/物理轴 |
| `opera/models/losses/limb_loss.py:23` | 14条连接：0–1、0–2、0–3、2–4、2–5、3–6、3–7、4–8、5–7、5–9、6–10、7–11、9–12、11–13 | 是14关节损失的数值索引连接，不构成解剖名称或坐标标定 |
| `visualization/visualize_24_pose.py:17` | BONES与上述损失连接相同 | 可追溯的24版可视化候选，不能自动继承其“metres”注释作为部署物理单位 |
| `opera/models/detectors/petr.py:374` | 通用14关节显示分支使用另一套12条连接，如0–2–4、1–3–5、6–8–10、7–9–11、12–13 | 与损失/24版可视化不一致，不能随意选用通用绘图分支 |
| `opera/datasets/wifi_pose.py:194` | keypoint_process内部还有另一份next_point表，但实际加载路径未调用 | 未执行函数不能当部署重排规范 |

当前可确定输出契约为100候选×14标签索引×3模型坐标。关节名称/轴向和哪份连接应作为最终展示标准待数据标签规范核对。
E1渲染方案讨论时应明确这一项，保持原始输出，无自动重排、平滑、坐标缩放或人体匹配。

### 候选排序

`petr_head.py:917`附近的原推理代码在分类分数上TopK，并用bbox_index抽取相应姿态。
当前ZG静态图TopK437输出值1137由Gather442作为索引输入（axis=0）；最终槽位经过排序，不是原query固定编号。
这支持“同槽位不能直接当作同一候选身份”的限制，尚不证明ONNX与板端大坐标差都来自排名变化。
本轮既有内容捕获可记录板端TopK索引；原ONNX只提供分数/姿态输出，未新增中间输出或安装onnx包。
跨端query身份对照仍待另定诊断范围，不使用最近姿态匹配改写原误差。

### VPU与RTSP

参考目录：`D:/Dowload from Chrome/嵌赛资料/Icraft/参考实现/单路PLIM+VPU/fpai_demo_package_26040702/fpai_demo_package_26040702`。

| 来源 | 原源码事实 | 接入需补齐 |
| --- | --- | --- |
| `deps/modelzoo_utils/include/pipeline/actor/vpu_encoder_actor.hpp:26` | 默认/dev/video0、1920×1080@60、NV21输入、HEVC/h265输出，6缓冲区；使用V4L2 Encoder | 首版要求720p H.264；须明确实际支持的输入格式、平面/stride与编码参数，不直接套默认值 |
| `examples/0_datapath/PLin+VPU/src/sdicamera+vpu2rtsp_server.cpp:102` | 读取fps/bitrate/codec/device，codec=h264时选择V4L2_PIX_FMT_H264_NO_SC；连接本地live555 sink | 原例为SDI相机输入，骨架画面应走PS生成数据路径，不能启动整个相机示例来代替接入 |
| 同文件:111–116 | 调用Device::Open及mmuModeSwitch(false) | 这些是会改变设备运行状态的示例初始化，本轮未调用，未来必须独立审查 |
| `deps/modelzoo_utils/include/pipeline/io/output/stream2rtsp_server.hpp:45`附近 | 首包按SPS/PPS处理，存在固定长度24/8与偏移4+20；流名liveH264 | 当前编码器输出的NAL边界、长度及缓冲区所有权须实测/审查，不能把参考假设当通用解析 |
| `examples/0_datapath/PLin+VPU/configs/ZG/sdicamera+vpu2rtsp_server.yaml` | 当前示例配置相机及VPU为1920×1080@60，RTSP URL为rtsp:// | 这是相机示例配置，不是已经核验的720p骨架编码配置 |

板上存在mvx驱动和video节点只证明驱动/节点可见，不证明实际H.264编码、RTSP播放或HDMI与VPU同时工作。

## 对后续开发的参考

先审查E0/N1/P1成果，再讨论E1网络接收与固定视角渲染的具体范围。视频先独立测试图，再接板端推理结果。
HDMI刷新率、编码帧率和有效骨架更新率分开统计，重复旧画面不算新推理；同一结果帧号应贯穿双路输出。
需单列PS渲染→RGB565显示、PS渲染→VPU所需格式两条转换和缓冲区所有权，不预设零拷贝或共享同一内存。
本轮资料整理完成，不宣称上述未确认项已解决；没有批准新的硬件初始化或视频应用执行。
