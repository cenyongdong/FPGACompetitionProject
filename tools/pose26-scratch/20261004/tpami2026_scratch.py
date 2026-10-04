"""Fresh-initialized pose-only training; never loads a model checkpoint."""
import json
from pathlib import Path

import torch
import torch.distributed as dist
from mmcv.runner import HOOKS

from opera.models.builder import DETECTORS
from opera.models.detectors.petr import PETR
from opera.models.tpami2026_transfer import PETR2026Transfer
from opera.models.transfer_support import PoseTransferOptimizerHook, module_norms


@DETECTORS.register_module()
class PETR2026Scratch(PETR2026Transfer):
    def __init__(self, *args, transfer_checkpoint=None, **kwargs):
        if transfer_checkpoint is not None:
            raise ValueError('Scratch training cannot accept a transfer checkpoint')
        super().__init__(*args, transfer_checkpoint=None, **kwargs)

    def init_weights(self):
        # Bypass PETR2026Transfer.init_weights, whose final action is migrate().
        PETR.init_weights(self)
        self.initialization_report = dict(
            mode='fresh_initialization', checkpoint_loaded=False,
            optimizer_restored=False, initialization_std=0.001,
            trainable_elements=sum(p.numel() for p in self.parameters() if p.requires_grad),
            module_parameter_l2=module_norms(self))


@HOOKS.register_module()
class PoseScratchOptimizerHook(PoseTransferOptimizerHook):
    def before_run(self, runner):
        model = runner.model.module
        assert dist.get_world_size() == self.expected_world == 4
        assert isinstance(runner.optimizer, torch.optim.Adam)
        assert not isinstance(runner.optimizer, torch.optim.AdamW)
        assert runner.epoch == 0 and runner.iter == 0
        assert len(runner.optimizer.state) == 0
        assert all(g['lr'] == 2e-5 and g['weight_decay'] == 1e-4
                   and tuple(g['betas']) == (0.9, 0.999)
                   for g in runner.optimizer.param_groups)
        if runner.rank == 0:
            report = dict(model.initialization_report)
            report['optimizer'] = dict(type='Adam', lr=2e-5, weight_decay=1e-4,
                                       betas=[0.9, 0.999], eps=1e-8,
                                       no_weight_decay_exclusions=True)
            Path(runner.work_dir, 'initialization.json').write_text(json.dumps(report, indent=2))

