"""Create the authorized isolated ten-epoch differentiation-only decay control."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OLD = PROJECT / 'tools/pose26-scratch/20261004'
REMOTE = 'tools/pose26_diff_nodecay'
RESULT = 'tpami2026_diff_nodecay_20261004'

def write(name, body):
    path = HERE / name
    path.write_text(body, encoding='utf-8', newline='\n')
    if path.suffix == '.py':
        ast.parse(body, filename=name)

write('petr_wifi_tpami2026_diff_nodecay.py', '''"""Ten-epoch scratch control: only differentiation parameters have zero decay."""
_base_ = ['./petr_wifi_tpami2026_scratch.py']
custom_imports = dict(imports=['opera.models.tpami2026_scratch',
                              'opera.models.tpami2026_diff_nodecay'], allow_failed_imports=False)
work_dir = 'result/tpami2026_diff_nodecay_20261004'
data = dict(val=dict(report_dir=work_dir), test=dict(report_dir=work_dir))
optimizer = dict(_delete_=True, type='Adam', lr=2e-5, betas=(0.9, 0.999),
                 eps=1e-8, weight_decay=1e-4,
                 constructor='PoseDiffNoDecayOptimizerConstructor')
optimizer_config = dict(_delete_=True, type='PoseDiffNoDecayOptimizerHook',
                        grad_clip=dict(max_norm=0.1, norm_type=2), interval=50, expected_world=4)
runner = dict(type='EpochBasedRunner', max_epochs=10)
''')

write('tpami2026_diff_nodecay.py', '''"""Optimizer-only control. Model, initialization and collapse gates stay unchanged."""
import json
from pathlib import Path
import torch
import torch.distributed as dist
from mmcv.runner import HOOKS
from mmcv.runner.optimizer.builder import OPTIMIZER_BUILDERS
from opera.models.transfer_support import PoseTransferOptimizerHook

PREFIX = 'bbox_head.transformer.joint_differentiators.'

def validate_groups(model, optimizer):
    named = dict(model.named_parameters())
    expected = {name for name in named if name.startswith(PREFIX)}
    assert len(expected) == 56, len(expected)
    seen = set()
    rows = []
    assert type(optimizer) is torch.optim.Adam
    assert len(optimizer.param_groups) == 2
    for group in optimizer.param_groups:
        names = group['parameter_names']
        assert len(names) == len(group['params']) and len(set(names)) == len(names)
        assert group['lr'] == 2e-5 and tuple(group['betas']) == (0.9, 0.999)
        assert group['eps'] == 1e-8
        for name, parameter in zip(names, group['params']):
            assert name not in seen and parameter is named[name]
            assert group['weight_decay'] == (0.0 if name in expected else 1e-4), name
            seen.add(name)
        rows.append(dict(parameter_names=names, tensors=len(names),
                         elements=sum(p.numel() for p in group['params']),
                         lr=group['lr'], weight_decay=group['weight_decay']))
    assert seen == set(named)
    return rows

@OPTIMIZER_BUILDERS.register_module()
class PoseDiffNoDecayOptimizerConstructor:
    def __init__(self, optimizer_cfg, paramwise_cfg=None):
        self.cfg = dict(optimizer_cfg)
        assert self.cfg.pop('type') == 'Adam'
        assert not paramwise_cfg
        assert self.cfg == dict(lr=2e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)

    def __call__(self, model):
        model = model.module if hasattr(model, 'module') else model
        groups = []
        for excluded in (True, False):
            items = [(n, p) for n, p in model.named_parameters()
                     if n.startswith(PREFIX) == excluded]
            groups.append(dict(params=[p for _, p in items],
                               parameter_names=[n for n, _ in items],
                               weight_decay=0.0 if excluded else 1e-4))
        optimizer = torch.optim.Adam(groups, **self.cfg)
        validate_groups(model, optimizer)
        return optimizer

@HOOKS.register_module()
class PoseDiffNoDecayOptimizerHook(PoseTransferOptimizerHook):
    def before_run(self, runner):
        model = runner.model.module
        assert dist.get_world_size() == self.expected_world == 4
        assert runner.epoch == 0 and runner.iter == 0
        assert len(runner.optimizer.state) == 0
        groups = validate_groups(model, runner.optimizer)
        if runner.rank == 0:
            report = dict(model.initialization_report)
            report['optimizer'] = dict(type='Adam', lr=2e-5, default_weight_decay=1e-4,
                                       zero_decay_prefix=PREFIX, betas=[0.9, 0.999], eps=1e-8)
            report['optimizer_groups'] = groups
            Path(runner.work_dir, 'initialization.json').write_text(json.dumps(report, indent=2))
''')

def derived(name):
    text = (OLD / name).read_text(encoding='utf-8')
    return text.replace('tpami2026_scratch_20261004', RESULT).replace(
        'tools/pose26_scratch', REMOTE).replace(
        'petr_wifi_tpami2026_scratch.py', 'petr_wifi_tpami2026_diff_nodecay.py')

unit = derived('verify_scratch.py')
unit = unit.replace('from opera.models import tpami2026_scratch',
                    'from opera.models import tpami2026_scratch, tpami2026_diff_nodecay\nfrom opera.models.tpami2026_diff_nodecay import PREFIX, validate_groups\nfrom mmcv.runner import build_optimizer')
unit = unit.replace("    optimizer = torch.optim.Adam(model.parameters(), lr=2e-5,\n                                 betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)",
                    '    optimizer = build_optimizer(model, cfg.optimizer)\n    groups = validate_groups(model, optimizer)')
unit = unit.replace("    assert all(g['lr'] == 2e-5 and g['weight_decay'] == 1e-4 for g in optimizer.param_groups)",
                    "    assert groups[0]['weight_decay'] == 0 and groups[1]['weight_decay'] == 1e-4")
unit = unit.replace('    optimizer.step()\n    losses = model', '''    before_diff = {n: p.detach().clone() for n, p in model.named_parameters() if n.startswith(PREFIX)}
    assert all(p.grad is not None and torch.count_nonzero(p.grad) == 0
               for n, p in model.named_parameters() if n.startswith(PREFIX))
    optimizer.step()
    assert all(torch.equal(before_diff[n], p) for n, p in model.named_parameters() if n.startswith(PREFIX))
    losses = model''')
unit = unit.replace("'passed': True, 'initialization'", "'passed': True, 'optimizer_groups': groups, 'zero_gradient_diff_parameters_unchanged': True, 'initialization'")
unit = unit.replace('    assert cfg.model.transfer_checkpoint is None', '''    reference = Config.fromfile(str(ROOT / 'configs/wifi/petr_wifi_tpami2026_scratch.py'))
    assert cfg.model == reference.model and cfg.data.train == reference.data.train
    for field in ('lr_config', 'checkpoint_config', 'evaluation', 'seed', 'load_from', 'resume_from'):
        assert cfg[field] == reference[field], field
    old_init = json.loads((ROOT / 'result/tpami2026_scratch_20261004/initialization.json').read_text())
    assert cfg.model.transfer_checkpoint is None''')
unit = unit.replace("    assert model.initialization_report['checkpoint_loaded'] is False", '''    assert model.initialization_report['checkpoint_loaded'] is False
    for key, norm in model.initialization_report['module_parameter_l2'].items():
        assert abs(norm - old_init['module_parameter_l2'][key]) < 1e-10, key''')
unit = unit.replace("if k != 'initialization'", "if k not in ('initialization', 'optimizer_groups')")
write('verify_diff_nodecay.py', unit)

smoke = derived('smoke_scratch.py')
write('smoke_diff_nodecay.py', smoke)
ddp = derived('verify-ddp-reviewed.py')
ddp = ddp.replace("==1\nassert all(g['lr']==2e-5 and g['weight_decay']==1e-4 for g in ck['optimizer']['param_groups'])", "==2\nassert [g['weight_decay'] for g in ck['optimizer']['param_groups']]==[0.0,1e-4]\nassert all(g['lr']==2e-5 for g in ck['optimizer']['param_groups'])\nassert init['optimizer']['zero_decay_prefix']=='bbox_head.transformer.joint_differentiators.'\nassert len(init['optimizer_groups'][0]['parameter_names'])==56")
ddp = ddp.replace("'no_weight_decay_exclusions':True", "'zero_decay_prefix':init['optimizer']['zero_decay_prefix'],'optimizer_groups':init['optimizer_groups']")
ddp = ddp.replace("if k!='diagnostics'", "if k not in ('diagnostics','optimizer_groups')")
write('verify_ddp.py', ddp)

run = derived('run_experiment.py')
run = run.replace('500-epoch', '10-epoch').replace('== 500', '== 10').replace(
    'approved_epochs=500', 'approved_epochs=10').replace('max_epochs=500', 'max_epochs=10').replace(
    'completed_500_epochs', 'completed_10_epochs')
run = run.replace("'paramwise_cfg' not in cfg.optimizer", "cfg.optimizer.constructor == 'PoseDiffNoDecayOptimizerConstructor'")
run = run.replace("'opera.models.tpami2026_scratch', 'opera.models.tpami2026_transfer',", "'opera.models.tpami2026_diff_nodecay', 'opera.models.tpami2026_scratch', 'opera.models.tpami2026_transfer',")
write('run_experiment.py', run)
launch = derived('launch-reviewed.py').replace("'max_epochs':500", "'max_epochs':10")
write('launch.py', launch)

final = derived('finalize.py')
final = final.replace('500 epochs', '10 epochs').replace('== 500', '== 10').replace(
    'range(1, 501)', 'range(1, 11)').replace('range(500)', 'range(10)').replace(
    'epoch_500.pth', 'epoch_10.pth').replace('completed_epochs=500', 'completed_epochs=10').replace(
    'fresh 500-epoch', 'fresh 10-epoch differentiation no-decay')
final = final.replace("abs(g['lr'] - 2e-6) < 1e-15 and g['weight_decay'] == 1e-4", "abs(g['lr'] - 2e-5) < 1e-15 and g['weight_decay'] == (0.0 if i == 0 else 1e-4)")
final = final.replace("for g in final['optimizer']['param_groups'])", "for i, g in enumerate(final['optimizer']['param_groups']))\n    assert len(final['optimizer']['param_groups']) == 2\n    assert all(__import__('torch').isfinite(x).all() for x in final['state_dict'].values())\n    assert all(__import__('torch').isfinite(x).all() for x in load_checkpoint_cpu(best[0])['state_dict'].values())")
final = final.replace("optimizer='Adam',", "optimizer='Adam', zero_decay_prefix='bbox_head.transformer.joint_differentiators.',")
final = final.replace("    report = dict(", '''    diagnostics = rows(OUT / 'branch_diagnostics.jsonl')
    def finite_tree(value):
        import math
        if isinstance(value, dict): return all(finite_tree(x) for x in value.values())
        if isinstance(value, list): return all(finite_tree(x) for x in value)
        if isinstance(value, (float, int)): return math.isfinite(value)
        return True
    assert diagnostics and all(finite_tree(x) for x in diagnostics)
    control_evaluations = rows(ROOT / 'result/tpami2026_scratch_20261004/evaluations.jsonl')
    control_parameters = rows(ROOT / 'result/tpami2026_scratch_20261004/epoch_parameter_checks.jsonl')
    matched_control = [dict(epoch=i+1, control_mpjpe_mm=row['metrics']['mpjpe'],
                           experiment_mpjpe_mm=evaluations[i]['metrics']['mpjpe'],
                           control_differentiation_l2=control_parameters[i]['parameter_l2']['differentiate'],
                           experiment_differentiation_l2=parameters[i]['parameter_l2']['differentiate'])
                       for i, row in enumerate(control_evaluations)]
    report = dict(diagnostic_count=len(diagnostics), matched_epoch_control=matched_control,
                  comparison_limitation='Single seed, 10 epochs; compare matched epochs, not convergence.', ''')
write('finalize.py', final)

write('PLAN.md', '''# 已批准的分化分支零衰减对照实验（2026-10-04）

仅将 bbox_head.transformer.joint_differentiators. 的全部56份权重/偏置设为 weight_decay=0；其余参数仍为1e-4。保留Adam、lr2e-5、betas(.9,.999)、eps1e-8；GPU1–4、每卡batch8/worker4、FP32、seed0、clip0.1、同样的数据和损失、14关节、3层vanilla细化、原初始化。全新模型/优化器，不加载任何checkpoint；正式训练10轮后停止讨论，不自动延长。450轮衰减计划保留，但本轮不会到达。对照基准为失败的500轮实验前5轮与第6轮退化诊断，不能将10轮从零结果直接当作与24版已收敛模型的公平终局比较。

新增独立配置、优化器构造器/初始化审计hook和管理脚本；不修改旧配置、模型结构或共享门禁。先核对准确分组、零监督梯度一步后分化参数逐元素不变、人物/关节索引及梯度，再用96样本进行四卡3步检查。正式重新初始化。非有限值、索引错误、DDP不一致或连续两轮分化/细化注意力L2<1e-10仍停止；禁止自动重启/改配置。用户暂不启用定时监测的选择及ID26暂停保持。
''')

mapping = {
    'configs/wifi/petr_wifi_tpami2026_diff_nodecay.py': 'petr_wifi_tpami2026_diff_nodecay.py',
    'configs/wifi/smoke_diff_nodecay.py': 'smoke_diff_nodecay.py',
    'opera/models/tpami2026_diff_nodecay.py': 'tpami2026_diff_nodecay.py',
}
for name in ('verify_diff_nodecay.py', 'verify_ddp.py', 'run_experiment.py', 'finalize.py', 'launch.py', 'PLAN.md'):
    mapping[REMOTE + '/' + name] = name
old_manifest = json.loads((OLD / 'manifest.json').read_text())
files = {remote: hashlib.sha256((HERE / local).read_bytes()).hexdigest() for remote, local in mapping.items()}
for remote in ('opera/models/tpami2026_scratch.py', 'configs/wifi/petr_wifi_tpami2026_scratch.py',
               'opera/models/tpami2026_transfer.py', 'opera/models/transfer_support.py',
               'configs/wifi/petr_wifi_tpami2026_transfer.py'):
    files[remote] = old_manifest['files'][remote]
write('manifest.json', json.dumps(dict(files=files, authorized=dict(epochs=10, optimizer='Adam',
        fresh_initialization=True, gpu_ids=[1,2,3,4], zero_decay_prefix='bbox_head.transformer.joint_differentiators.')), indent=2))
mapping[REMOTE + '/manifest.json'] = 'manifest.json'
write('upload-map.json', json.dumps(mapping, indent=2))
print(json.dumps(dict(generated_files=len(mapping), directory=str(HERE))))
