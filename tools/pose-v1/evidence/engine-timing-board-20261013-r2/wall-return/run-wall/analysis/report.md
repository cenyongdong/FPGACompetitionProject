# Engine计时分析

状态：finite_numeric_timing_evidence

| Engine阶段 | 均值/ms | P95/ms | 最大/ms |
|---|---:|---:|---:|
| process_ms | 195.098357 | 195.810060 | 195.810060 |
| forward_ms | 187.616973 | 188.148480 | 188.148480 |
| preprocess_ms | 5.621643 | 5.648980 | 5.648980 |
| input_prepare_ms | 0.056847 | 0.080170 | 0.080170 |
| state_clear_ms | 0.004660 | 0.005150 | 0.005150 |
| final_wait_ms | 0.226653 | 0.243500 | 0.243500 |
| output_read_ms | 1.257450 | 1.394410 | 1.394410 |
| selection_ms | 0.001120 | 0.001200 | 0.001200 |
| actual_save_ms | 0.487200 | 0.528200 | 0.528200 |
| comparison_ms | 0.012617 | 0.013070 | 0.013070 |

下面是含子区间的观测跨度，不能与上表直接相加。

| 观测跨度 | 墙钟均值/ms | 线程CPU均值/ms |
|---|---:|---:|
| bridge.allocate:188 | 0.021940 | 0.022233 |
| bridge.allocate:192 | 0.020277 | 0.020390 |
| bridge.allocate:437 | 0.017183 | 0.017447 |
| bridge.allocate:582 | 0.024238 | 0.024588 |
| bridge.allocate:649 | 0.022753 | 0.023090 |
| bridge.copy:188 | 0.095310 | 0.094917 |
| bridge.copy:192 | 0.103000 | 0.102725 |
| bridge.copy:437 | 0.079773 | 0.079470 |
| bridge.copy:582 | 0.096667 | 0.096470 |
| bridge.copy:649 | 0.098242 | 0.098047 |
| bridge.counter_wait:582 | 0.023420 | 0.023823 |
| bridge.cpu:188 | 0.334013 | 0.333967 |
| bridge.cpu:192 | 2.468077 | 2.417307 |
| bridge.cpu:437 | 0.263293 | 0.263330 |
| bridge.cpu:582 | 5.539427 | 5.517720 |
| bridge.cpu:649 | 5.516317 | 5.516457 |
| bridge.spec:188 | 0.037280 | 0.037470 |
| bridge.spec:192 | 0.029517 | 0.029750 |
| bridge.spec:437 | 0.026140 | 0.026393 |
| bridge.spec:582 | 0.034933 | 0.035193 |
| bridge.spec:649 | 0.034900 | 0.035190 |
| bridge.wait:188 | 3.837920 | 3.780290 |
| bridge.wait:192 | 0.006640 | 0.005983 |
| bridge.wait:437 | 3.072517 | 3.068573 |
| bridge.wait:582 | 41.485258 | 41.440462 |
| bridge.wait:649 | 36.199882 | 36.083298 |
| op.host:0 | 0.136370 | 0.082827 |
| op.host:188 | 5.022453 | 4.964820 |
| op.host:192 | 3.761177 | 3.710423 |
| op.host:437 | 3.955960 | 3.951600 |
| op.host:442 | 0.984823 | 0.985427 |
| op.host:582 | 89.606443 | 89.495577 |
| op.host:649 | 78.994793 | 78.761910 |
| op.zg:9185 | 0.258843 | 0.259020 |
| op.zg:9186 | 0.098550 | 0.098677 |
| op.zg:9187 | 0.115720 | 0.115867 |
| op.zg:9188 | 0.032680 | 0.032613 |
| op.zg:9189 | 0.133733 | 0.133980 |
| op.zg:9190 | 0.164360 | 0.144667 |
| op.zg:9191 | 0.172403 | 0.172590 |
| runtime.final_wait | 0.226807 | 未知 |
| runtime.forward | 187.617473 | 未知 |
| runtime.input_prepare | 0.057087 | 未知 |
| runtime.input_validation | 0.147547 | 0.147137 |
| runtime.output_read | 1.257783 | 未知 |
| runtime.preprocess | 5.621917 | 未知 |
| runtime.raw_validation | 0.105093 | 0.105173 |
| runtime.selection | 0.001410 | 未知 |
| runtime.state_clear | 0.004837 | 未知 |
| runtime.total | 195.149343 | 192.413870 |

forward_partitions中的残余为调度、回调与未覆盖工作的混合量。
硬件层计时及SDK原始字段是独立证据，不参与墙钟饼图或直接扣减。

## 测量限制

- bridge.wait为等待输入ready的宿主墙钟，不能全部归因NPU、DDR或SDK。
- 硬件层计时包含算术、内部访存及可能的停顿，缺少独立DDR-stall计数。
- SDK四项tuple单位及跨forward累积语义未确认；保留raw，不与ms相减。
- SDK调用残余包含调度、回调观测和未覆盖工作，不能视为精确SDK调度时间。
- 墙钟减线程CPU包括阻塞、抢占等；上下文切换计数不提供调度等待时长。
- 逻辑搬运字节不是PL DDR总通信量，有效API吞吐不是DDR总线带宽。
- 诊断采样、SDK profiling与输出落盘会扰动运行；baseline/wall/sdk须独立比较。
- 本入口无VPU/TCP并发负载，结果不外推整机稳定性、5Hz或长期验收。

## 同身份基线比较

```json
{
  "process_ms": {
    "baseline_mean_ms": 195.92257999999998,
    "instrumented_mean_ms": 195.09835666666666,
    "difference_ms": -0.8242233333333218,
    "ratio": 0.9957931171928559
  },
  "forward_ms": {
    "baseline_mean_ms": 186.71815666666666,
    "instrumented_mean_ms": 187.61697333333333,
    "difference_ms": 0.8988166666666757,
    "ratio": 1.0048137614611914
  },
  "interpretation": "Sequential run comparison; includes run variation, not an exact correction factor."
}
```
