"""Recompute per-forward timing from accepted raw spans; never sum invalid SDK timers."""
from pathlib import Path
import collections
import json
import statistics

ROOT = Path(__file__).resolve().parent
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def mean(xs):
    return statistics.mean(xs)

wall = ROOT / 'wall-return/run-wall'
report = read(wall / 'analysis/report.json')
assert report['status'] == 'finite_numeric_timing_evidence'
rows = [r for r in lines(wall / 'results/monotonic-spans.jsonl') if r['invocation'] < 3]
aggregate = {}
for kind in sorted({r['kind'] for r in rows}):
    chosen = [r for r in rows if r['kind'] == kind]
    durations = [sum(r['end_ns']-r['begin_ns'] for r in chosen if r['invocation']==i)/1e6 for i in range(3)]
    cpu = [sum(r['thread_cpu_ns'] for r in chosen if r['invocation']==i)/1e6 for i in range(3)] if all(r.get('thread_cpu_ns') is not None for r in chosen) else None
    aggregate[kind] = {'wall_mean_ms':mean(durations), 'thread_cpu_mean_ms':mean(cpu) if cpu else None, 'per_forward_ms':durations}
partitions = report['forward_partitions']
ops = []
for op_id in (0,188,192,437,442,582,649):
    samples = [next(o for o in p['operators'] if o['op_id']==op_id) for p in partitions]
    ops.append({'op_id':op_id, 'inclusive_ms':mean([s['inclusive_ns']/1e6 for s in samples]),
                'thread_cpu_ms':mean([s['thread_cpu_ns']/1e6 for s in samples]),
                'unattributed_ms':mean([s['unattributed_ns']/1e6 for s in samples]),
                'bridge_phases_ms':{k:mean([s['bridge_phases_ns'][k]/1e6 for s in samples]) for k in samples[0]['bridge_phases_ns']}})
transfer = lines(wall / 'results/transfers.jsonl')
logical_bytes = sum(t['logical_bytes'] for t in transfer)/3
hw = lines(ROOT / 'sdk-return/run-sdk/results/hardware-layers.jsonl')[0]
negative = [{'zero_based_index':i,'ms':v} for i,v in enumerate(hw['values']) if v<0]
failure = read(ROOT / 'sdk-return/run-sdk/results/failure.json')
baseline = read(ROOT / 'baseline-return/run-baseline/analysis/report.json')
result = {'date':'2026-10-13','conditions':{'windows':[308,309,310],'samples_per_accepted_mode':3,'warmup':0,'VPU_TCP_load':False,'probe_overhead_included':True},
          'wall_init_ms':report['summary']['init_ms'], 'baseline_init_ms':baseline['summary']['init_ms'],
          'frame_metric_ms':report['frame_metric_ms'], 'aggregate_per_forward':aggregate,'host_operators':ops,
          'forward_outside_callback_mean_ms':mean([p['dispatch_callbacks_and_unobserved_ns']/1e6 for p in partitions]),
          'host_outside_bridge_mean_ms':sum(o['unattributed_ms'] for o in ops),
          'copy_logical_bytes_per_forward':logical_bytes,
          'copy_effective_API_MB_s':logical_bytes/(aggregate['bridge.copy']['wall_mean_ms']*1000),
          'wait_fraction_of_process_percent':aggregate['bridge.wait']['wall_mean_ms']/report['frame_metric_ms']['process_ms']['mean']*100,
          'baseline_process_ms':baseline['frame_metric_ms']['process_ms']['mean'],
          'baseline_forward_ms':baseline['frame_metric_ms']['forward_ms']['mean'],
          'sdk_failed_batch':{'failure':failure,'hardware_count':len(hw['values']),'negative_count':len(negative),'negative_values':negative,'min_ms':min(hw['values']),'max_ms':max(hw['values']),'session_total_ms':hw['session_total_ms'],'collection_ms':hw['collection_ms'],'hardware_sum_ms':None,'layer_ordinal_mapping_verified':False},
          'pure_NPU_compute_ms':None,'DDR_stall_ms':None,'exact_SDK_dispatch_ms':None}
partition_total = sum(aggregate[k]['wall_mean_ms'] for k in ('bridge.wait','bridge.cpu','bridge.copy','bridge.allocate','bridge.spec','bridge.counter_wait')) + result['host_outside_bridge_mean_ms'] + aggregate['op.zg']['wall_mean_ms'] + result['forward_outside_callback_mean_ms']
assert abs(partition_total-aggregate['runtime.forward']['wall_mean_ms']) < 1e-9
assert len(transfer)==24 and logical_bytes==115360 and len(negative)==215
(ROOT/'timing-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text = ['# Engine计时实测表（2026-10-13）', '',
        'Lite板端，固定308/309/310三个窗口；baseline/wall各3次，无预热、无VPU/TCP并发，含诊断采样开销。实际输出先完整保存后逐位比较，两模式共6次通过。SDK模式第一帧输出正确，但采集到非法层计时，停止且未重试。', '',
        '| Engine阶段 | 单次均值（ms） | 口径 |', '|---|---:|---|']
labels = [('process_ms','Engine处理总计','不含初始化及测试输出落盘/比较'),
          ('preprocess_ms','预处理','宿主墙钟'),('input_prepare_ms','输入准备','宿主墙钟'),
          ('state_clear_ms','状态复位','宿主墙钟'),('forward_ms','Session.forward','包含下面的嵌套细项'),
          ('final_wait_ms','末端输出等待','宿主墙钟'),('output_read_ms','输出读取/校验','宿主墙钟'),
          ('selection_ms','候选选择','宿主墙钟')]
for key,label,note in labels:
    text.append(f"| {label} | {result['frame_metric_ms'][key]['mean']:.3f} | {note} |")
text.extend(['',f"wall模式冷初始化：{result['wall_init_ms']/1000:.3f}s；baseline冷初始化：{result['baseline_init_ms']/1000:.3f}s。测试输出落盘{result['frame_metric_ms']['actual_save_ms']['mean']:.3f}ms、逐位比较{result['frame_metric_ms']['comparison_ms']['mean']:.3f}ms均在Engine处理外。", '',
             '| forward内部分解 | 单次均值（ms） | 解释 |','|---|---:|---|'])
for kind,label,note in [('bridge.wait','CPU桥等待输入ready','不能等同纯NPU计算'),
                        ('bridge.cpu','已观测CPU核执行','五个自定义桥算子的核区间；Gather442另在回调剩余内'),
                        ('bridge.copy','设备→Host搬运API','包含API开销，非独立DDR访存时间'),
                        ('bridge.allocate','桥内分配','宿主墙钟'),('bridge.spec','张量规格检查','宿主墙钟'),
                        ('bridge.counter_wait','完成计数等待','宿主墙钟')]:
    text.append(f"| {label} | {aggregate[kind]['wall_mean_ms']:.3f} | {note} |")
text.extend([f"| Host回调其他区间 | {result['host_outside_bridge_mean_ms']:.3f} | 包括原Gather442、回调观测及未覆盖工作 |",
             f"| ZG回调提交区间 | {aggregate['op.zg']['wall_mean_ms']:.3f} | 异步提交回调，非NPU硬件执行 |",
             f"| forward回调外剩余 | {result['forward_outside_callback_mean_ms']:.3f} | 包括SDK调度与未覆盖工作，不能独立归因 |", '',
             '分解用原始trace区间并集，合计187.617473ms；Engine内forward计时187.616973ms，边界探针相差约0.0005ms。两张表是嵌套关系，不跨表相加。', '',
             '| Host算子 | 回调整体（ms） | 输入等待（ms） | 独立CPU核区间（ms） |','|---|---:|---:|---:|'])
for o,label in zip(ops[1:],('TopK188','GatherElements192','TopK437','原Gather442','ScatterND582','ScatterND649')):
    phases=o['bridge_phases_ms']
    wait = f"{phases['bridge.wait']:.3f}" if o['op_id']!=442 else '未独立测量'
    cpu = f"{phases['bridge.cpu']:.3f}" if o['op_id']!=442 else '未独立测量'
    text.append(f"| {label} | {o['inclusive_ms']:.3f} | {wait} | {cpu} |")
text.extend(['',f"桥输入等待占Engine总时间{result['wait_fraction_of_process_percent']:.2f}%，期间主线程CPU时间{aggregate['bridge.wait']['thread_cpu_mean_ms']:.3f}ms，表明等待区间存在大量CPU活动；不能据此分离NPU算术/DDR/调度。",
             f"每次观测到8次device_to_host搬运，逻辑字节{logical_bytes:.0f}B，API有效吞吐{result['copy_effective_API_MB_s']:.3f}MB/s；不是DDR总线带宽。", '',
             '| 当前不能可靠获得的时间 | 状态 |','|---|---|',
             '| NPU硬件执行总计/纯算术 | getLayerTime(745)返回745项，其中215项为负；不得求和或只取有效前缀 |',
             '| DDR内部访存/停顿 | 无独立公开计数，不能用搬运API时间替代 |',
             '| 精确SDK调度 | 回调外剩余不能完全归因调度；SDK tuple单位/累积语义未确认 |', '',
             f"失败SDK阶段Session.totalTime原值{hw['session_total_ms']:.5f}ms，硬件采集调用{hw['collection_ms']:.5f}ms；只是失败批次单样本，不作为有效NPU总时间。负值根因尚未确认。", '',
             'baseline均值：Engine195.922580ms、forward186.718157ms；wall为195.098357ms、187.616973ms。首帧预处理波动及采样影响使模式差不能当精确探针开销。仅3样本，不外推长期、并发或严格整机5Hz。', '',
             '完整原值：[wall结果](wall-return/run-wall/results/monotonic-spans.jsonl)、[wall分析](wall-return/run-wall/analysis/report.json)、[SDK失败](sdk-return/run-sdk/results/failure.json)、[硬件原值](sdk-return/run-sdk/results/hardware-layers.jsonl)、[汇总JSON](timing-summary.json)。历史164.456893ms等待来自2026-10-07另批30帧，不与本批相加。', ''])
(ROOT/'timing-table.md').write_text('\n'.join(text),encoding='utf-8')
print(json.dumps({'status':'summary_written','engine_ms':result['frame_metric_ms']['process_ms']['mean'],
                  'wait_ms':aggregate['bridge.wait']['wall_mean_ms'],'sdk_negative_count':len(negative)},ensure_ascii=False))
