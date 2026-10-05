"""Generate the local verified result summary from captured evidence only."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / 'evidence/completion-20261004-1306'
verify = json.loads((HERE/'evidence/completion-verification.json').read_text())
report = json.loads((RAW/'final-report.json').read_text())
assert verify['passed'] and report['completed_epochs'] == 10
evals = report['evaluations']
checks = report['epoch_parameter_checks']
lines = ['# 分化分支零衰减10轮：完成核验与结果（2026-10-04）', '',
         '## 工程内容总结', '',
         '**12:00:59完成10轮/28,110步并停止，13:06完成独立核验；训练完成不等于细化分支有效或精度达标。** 监督、torchrun及四个rank退出，GPU1–4空闲，无自动延长/重试。用户暂不启用定时监测的选择保持，未更改ID26。', '',
         '实验只将Differentiation Branch的56份权重/偏置衰减设为0，其他参数仍为1e-4；Adam lr2e-5、全新初始化、seed0、四卡batch32、原结构/初始化/数据/损失不变。具体实现、命令和范围见同目录README及PLAN。', '',
         '10次全7824帧评估、10次四卡一致性检查、563条有限诊断、134份源码/快照和解析配置哈希通过；最佳和最终checkpoint的参数与优化器状态有限、元数据/分组及SHA256通过，CSV与曲线产物存在并核对。权重保留服务器，未复制到本机或部署。', '',
         '### 精度与同轮对照', '',
         '| 轮次 | 本次MPJPE/mm | 原全衰减MPJPE/mm | 原值−本次/mm | 分化L2 |',
         '| --- | ---: | ---: | ---: | ---: |']
control = {x['epoch']: x for x in verify['comparisons']}
for i, ev in enumerate(evals, 1):
    old = control.get(i)
    lines.append(f"| {i} | {ev['metrics']['mpjpe']:.6f} | " +
                 (f"{old['control_mm']:.6f} | {old['improvement_mm']:.6f}" if old else '无评估 | —') +
                 f" | {checks[i-1]['parameter_l2']['differentiate']:.9f} |")
best = verify['best_evaluation']
last = verify['final_evaluation']
stage = best['fixed_final_pairing_stage_mpjpe']
lines += ['', f"最佳第6轮 **{verify['best_mpjpe_mm']:.6f} mm**；第10轮 **{verify['final_mpjpe_mm']:.6f} mm**，较最佳回升{verify['final_mpjpe_mm']-verify['best_mpjpe_mm']:.6f} mm。",
          '原实验第6轮停止且没有评估，因此不能把跨轮最佳值差异当作严格同轮改善。前5轮对照有改善也有退步，不证明稳定精度收益。24版已收敛基准123.085352129mm仅为参考；不能将10轮从零实验当作500轮架构能力的终局评价。', '',
          '### 人数分组（最佳第6轮）', '', '| 人数 | 帧数 | MPJPE/mm |', '| --- | ---: | ---: |']
for n, item in best['by_person_count'].items():
    lines.append(f"| {n} | {item['frames']} | {item['mpjpe']:.6f} |")
lines += ['', '### 逐关节结果', '', '下面使用数据原始关节索引0–13，不自行推定解剖名称；坐标物理轴对应尚未确认。', '',
          '| 关节索引 | 第6轮/mm | 第10轮/mm |', '| --- | ---: | ---: |']
for i, (a, b) in enumerate(zip(best['per_joint_mm'], last['per_joint_mm'])):
    lines.append(f'| {i} | {a:.6f} | {b:.6f} |')
lines += ['', '### 固定最终匹配下的粗→细化', '', '| 阶段 | 第6轮/mm | 第10轮/mm |', '| --- | ---: | ---: |']
for name, a, b in zip(('粗姿态', '细化1', '细化2', '细化3'), stage, last['fixed_final_pairing_stage_mpjpe']):
    lines.append(f'| {name} | {a:.6f} | {b:.6f} |')
lines += ['', f'最佳轮粗→细化仅改善{stage[0]-stage[-1]:.6f}mm；该指标使用原GT辅助greedy100候选及固定最终匹配，不是部署人数选择验收。', '',
          '### 分支学习状态与门禁限制', '',
          '分化L2从初始化1.357186增长并停在1.908233679，第5–10轮未再变化到记录精度；查询残差RMS仍约0.00519，权重和残差没有归零。但第6轮第15351步首次抽检到分化/细化注意力梯度同时为0；第7–10轮全部抽检均为0。这里是抽检结果，不能断言两个抽检间每一步均为0。', '',
          '末轮细化注意力参数L2仍约21.73，坐标回归L2从初始化22.665降至0.01530；末次回归梯度非零。说明仅保存分化权重范数，仍未维持整条细化梯度通路。其他细化参数的衰减/激活/反向传播关系需要进一步定位，不能仅由这些范数唯一归因。', '',
          '现有Persistent branch collapse门禁检查的是分化/细化注意力参数L2连续两轮小于1e-10；本次两者没有触发该阈值，因此正常完成。它并未覆盖“参数非零但梯度长期为零”的退化。没有为了完成训练修改门禁，后续增加门禁或改参数仍须先讨论批准。', '',
          '### 权重与证据', '']
for item in verify['weights']:
    lines += [f"- {item['kind']}: `{item['path']}`；epoch={item['epoch']}、iter={item['iterations']}、{item['bytes']}字节；SHA256 `{item['sha256']}`。"]
lines += ['', '独立核验：[completion-verification.json](D:/FPGACompetitionProject/tools/pose26-diff-nodecay/20261004/evidence/completion-verification.json)。原始报告、CSV/曲线、日志和诊断：[原始证据目录](D:/FPGACompetitionProject/tools/pose26-diff-nodecay/20261004/evidence/completion-20261004-1306/final-report.json)。', '',
          '[训练曲线](D:/FPGACompetitionProject/tools/pose26-diff-nodecay/20261004/evidence/completion-20261004-1306/training-curves.png)', '',
          '## 对后续开发的参考', '',
          '本次单变量、单seed对照支持分化衰减与原权重塌缩有关：本次分化权重未消失并越过了第6轮参数范数停止点。但仅关闭该部分仍不足以恢复长期细化学习，不能因此批准继续500轮或扩大零衰减范围。后续应先定位坐标回归分支及细化反向通路，并将参数、梯度、激活/残差和同匹配粗细化误差一起判断；任何新实验或修复先讨论批准。', '',
          '训练当前已结束，禁止重复启动、自动恢复/延长或静默切换优化器。本次未进行ONNX/Icraft/NPU/FPGA部署。']
(HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
print('RESULTS_WRITTEN')
