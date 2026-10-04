"""Audited pose-only migration, diagnostics, and unchanged legacy MPJPE.

This module is deployed as opera.models.transfer_support. No mesh code.
"""
import collections
import hashlib
import json
import os
import pickle
import types
from pathlib import Path

import numpy as np
import torch
import torch.distributed as dist
from mmcv.runner import HOOKS, OptimizerHook
from mmcv.runner.optimizer.builder import OPTIMIZER_BUILDERS
from opera.datasets.builder import DATASETS
from opera.datasets.wifi_pose import WifiPoseDataset

SOURCE_SHA256 = '6493e2250b83aef59ce4825e15d2d0043a59490275f75933f9a59867867d3221'
PREFIXES = ('bbox_head.transformer.encoder.', 'bbox_head.transformer.decoder.',
            'bbox_head.cls_branches.', 'bbox_head.kpt_branches.',
            'bbox_head.query_embedding.', 'head.projection.')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_checkpoint_cpu(path):
    # Permit the known tensor/NumPy-scalar globals in these user checkpoints.
    allowed = {('collections', 'OrderedDict'): collections.OrderedDict,
               ('numpy.core.multiarray', 'scalar'): np.core.multiarray.scalar,
               ('numpy', 'dtype'): np.dtype,
               ('torch._utils', '_rebuild_tensor_v2'): torch._utils._rebuild_tensor_v2}
    for name in ('FloatStorage', 'LongStorage', 'DoubleStorage', 'HalfStorage', 'ByteStorage'):
        allowed[('torch', name)] = getattr(torch, name)

    class Restricted(pickle.Unpickler):
        def find_class(self, module, name):
            if (module, name) not in allowed:
                raise pickle.UnpicklingError('Unexpected checkpoint global: ' + module + '.' + name)
            return allowed[(module, name)]

    module = types.ModuleType('restricted_checkpoint_reader')
    module.Unpickler = Restricted
    module.load = pickle.load
    return torch.load(path, map_location='cpu', pickle_module=module)


def migrate(model, checkpoint):
    actual = digest(checkpoint)
    if actual != SOURCE_SHA256:
        raise RuntimeError('Source checkpoint hash changed: ' + actual)
    source = load_checkpoint_cpu(checkpoint)
    if source['meta']['epoch'] != 442:
        raise RuntimeError('Unexpected baseline epoch')
    target = model.state_dict()
    copied = {}
    for key, value in source['state_dict'].items():
        name = 'head.projection.' + key[5:] if key.startswith('head.') else key
        if name.startswith(PREFIXES):
            if name not in target or target[name].shape != value.shape:
                raise RuntimeError('Migration shape/key mismatch: ' + name)
            copied[name] = value
    expected = {name for name in target if name.startswith(PREFIXES)}
    if set(copied) != expected or len(copied) != 169:
        raise RuntimeError('Incomplete migration')
    model.load_state_dict(copied, strict=False)
    for name, value in copied.items():
        if not torch.equal(model.state_dict()[name].cpu(), value):
            raise RuntimeError('Migration value mismatch: ' + name)
    model.transfer_report = {'source': str(checkpoint), 'sha256': actual,
                             'epoch': 442, 'loaded': sorted(copied),
                             'tensor_count': len(copied),
                             'elements': sum(x.numel() for x in copied.values()),
                             'optimizer_restored': False}


@OPTIMIZER_BUILDERS.register_module()
class PoseTransferOptimizerConstructor:
    def __init__(self, optimizer_cfg, paramwise_cfg=None):
        self.cfg = dict(optimizer_cfg)
        assert self.cfg.pop('type') == 'AdamW'
        assert not paramwise_cfg

    def __call__(self, model):
        model = model.module if hasattr(model, 'module') else model
        groups = []
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            transferred = name.startswith(PREFIXES)
            no_decay = (param.ndim <= 1 or 'joint_differentiators.' in name
                        or name == 'head.ste' or 'query_embedding.' in name)
            groups.append({'params': [param], 'lr': 2e-6 if transferred else 2e-5,
                           'weight_decay': 0.0 if no_decay else 1e-4,
                           'parameter_name': name, 'transferred': transferred})
        return torch.optim.AdamW(groups, **self.cfg)


def distributed_ok(condition, device, message):
    flag = torch.tensor(0 if condition else 1, device=device, dtype=torch.int32)
    if dist.is_initialized():
        dist.all_reduce(flag, op=dist.ReduceOp.MAX)
    if flag.item():
        raise RuntimeError(message)


def module_norms(model, gradients=False):
    groups = {'differentiate': 'bbox_head.transformer.joint_differentiators.',
              'refine_attention': 'bbox_head.transformer.refine_decoder.',
              'refine_regression': 'bbox_head.refine_kpt_branches.',
              'pose_decoder': 'bbox_head.transformer.decoder.', 'ste': 'head.ste'}
    out = {}
    for name, prefix in groups.items():
        tensors = [(p.grad if gradients else p).detach().double()
                   for k, p in model.named_parameters()
                   if k.startswith(prefix) and (not gradients or p.grad is not None)]
        out[name] = float(torch.stack([x.square().sum() for x in tensors]).sum().sqrt()) if tensors else 0.0
    return out


@HOOKS.register_module()
class PoseTransferOptimizerHook(OptimizerHook):
    """Same backward/clip/step order, with finite and collapse checks."""
    def __init__(self, grad_clip, interval=50, expected_world=4):
        super().__init__(grad_clip=grad_clip)
        self.interval = interval
        self.expected_world = expected_world
        self.collapsed_epochs = 0

    def before_run(self, runner):
        model = runner.model.module
        assert dist.get_world_size() == self.expected_world
        if runner.rank == 0:
            report = dict(model.transfer_report)
            report['optimizer_groups'] = [{k: v for k, v in g.items() if k != 'params'}
                                           for g in runner.optimizer.param_groups]
            Path(runner.work_dir, 'migration.json').write_text(json.dumps(report, indent=2))

    def after_train_iter(self, runner):
        model = runner.model.module
        loss = runner.outputs['loss']
        distributed_ok(bool(torch.isfinite(loss)), loss.device, 'Non-finite loss')
        count = runner.outputs['num_samples']
        assert count == 8 or (runner.inner_iter + 1 == len(runner.data_loader)
                              and 1 <= count <= 8), 'Unexpected per-rank batch'
        runner.optimizer.zero_grad()
        loss.backward()
        audit = runner.iter % self.interval == 0
        before = module_norms(model, gradients=True) if audit else None
        grad_norm = self.clip_grads(model.parameters())
        distributed_ok(bool(torch.isfinite(grad_norm)), loss.device, 'Non-finite gradient norm')
        after = module_norms(model, gradients=True) if audit else None
        runner.optimizer.step()
        runner.log_buffer.update({'grad_norm': float(grad_norm)}, runner.outputs['num_samples'])
        if audit:
            norms = module_norms(model)
            distributed_ok(all(np.isfinite(v) for v in norms.values()), loss.device, 'Non-finite parameters')
            if runner.rank == 0:
                row = {'epoch': runner.epoch + 1, 'iter': runner.iter + 1,
                       'gradient_before_clip': before, 'gradient_after_clip': after,
                       'parameter_l2': norms,
                       'queries': {k: float(v) for k, v in model.bbox_head.transformer.query_diagnostics.items()}}
                with open(Path(runner.work_dir, 'branch_diagnostics.jsonl'), 'a') as f:
                    f.write(json.dumps(row) + '\n')

    def after_train_epoch(self, runner):
        model = runner.model.module
        norms = module_norms(model)
        values = torch.tensor(list(norms.values()), device=next(model.parameters()).device, dtype=torch.float64)
        gathered = [torch.empty_like(values) for _ in range(dist.get_world_size())]
        dist.all_gather(gathered, values)
        assert all(torch.allclose(values, x, rtol=1e-7, atol=1e-9) for x in gathered), 'DDP parameter divergence'
        collapsed = norms['differentiate'] < 1e-10 or norms['refine_attention'] < 1e-10
        self.collapsed_epochs = self.collapsed_epochs + 1 if collapsed else 0
        distributed_ok(self.collapsed_epochs < 2, values.device, 'Persistent branch collapse')
        if runner.rank == 0:
            with open(Path(runner.work_dir, 'epoch_parameter_checks.jsonl'), 'a') as f:
                f.write(json.dumps({'epoch': runner.epoch + 1, 'parameter_l2': norms, 'ddp_equal': True}) + '\n')


def legacy_pairing(gt, pred):
    # Same greedy distance/sentinel/tie order as WifiPoseDataset.calc_mpjpe.
    distances = torch.norm(gt[:, None] - pred[None], p=2, dim=-1).mean(-1)
    if not torch.isfinite(distances).all():
        raise RuntimeError('Non-finite evaluation prediction')
    assigned = torch.full((len(gt),), -1, dtype=torch.long)
    occupied = torch.zeros(len(pred), dtype=torch.bool)
    while distances.min() < 50:
        rows, cols = torch.where(distances == distances.min())
        for row, col in zip(rows.tolist(), cols.tolist()):
            distances[row, col] = 50
            if assigned[row] < 0 and not occupied[col]:
                assigned[row] = col
                occupied[col] = True
    if (assigned < 0).any():
        raise RuntimeError('Unmatched GT: refusing legacy pred[-1] fallback')
    return assigned


@DATASETS.register_module()
class WifiPoseTransferAuditDataset(WifiPoseDataset):
    def __init__(self, *args, report_dir=None, limit_samples=None, **kwargs):
        super().__init__(*args, **kwargs)
        if limit_samples is not None:
            self.filename_list = self.filename_list[:limit_samples]
            self._set_group_flag()
        self.report_dir = report_dir
        self.eval_round = 0

    def evaluate(self, results, **kwargs):
        assert len(results) == len(self.filename_list)
        metrics, joints, grouped, stages = [], [], collections.defaultdict(list), []
        for sample_id, result in zip(self.filename_list, results):
            legacy = result['legacy'] if isinstance(result, dict) else result
            gt = torch.tensor(np.load(Path(self.data_root, 'keypoint', sample_id + '.npy'), allow_pickle=False), dtype=torch.float32)
            pred = torch.tensor(legacy[1][0], dtype=torch.float32)
            pair = legacy_pairing(gt, pred)
            # Original routine remains the source of the reported main metric.
            original = self.calc_mpjpe(gt, pred, sample_id, root=[5, 7])
            errors = torch.norm(gt - pred[pair], dim=-1) * 1000
            assert abs(float(errors.mean()) - float(original[0])) < 1e-3
            metrics.append([float(x) for x in original])
            joints.append(errors.mean(0).tolist())
            grouped[len(gt)].append(float(original[0]))
            if isinstance(result, dict):
                stages.append([float(torch.norm(gt - torch.tensor(s)[pair], dim=-1).mean() * 1000)
                               for s in result['stages']])
        avg = np.mean(metrics, axis=0)
        output = collections.OrderedDict(zip(('mpjpe', 'mpjpeh', 'mpjpev', 'mpjped'), avg.tolist()))
        self.eval_round += 1
        record = {'evaluation_round': self.eval_round, 'frames': len(results), 'metrics': output,
                  'per_joint_mm': np.mean(joints, axis=0).tolist(),
                  'by_person_count': {str(k): {'frames': len(v), 'mpjpe': float(np.mean(v))} for k, v in grouped.items()},
                  'fixed_final_pairing_stage_mpjpe': np.mean(stages, axis=0).tolist() if stages else None,
                  'axis_convention': 'original_columns_physical_axes_unconfirmed',
                  'metric_protocol': 'legacy_greedy_all_100_candidates_frame_mean'}
        if self.report_dir:
            Path(self.report_dir).mkdir(parents=True, exist_ok=True)
            with open(Path(self.report_dir, 'evaluations.jsonl'), 'a') as f:
                f.write(json.dumps(record) + '\n')
        print('POSE_AUDIT ' + json.dumps(record), flush=True)
        return output
