"""Optimizer-only control. Model, initialization and collapse gates stay unchanged."""
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
