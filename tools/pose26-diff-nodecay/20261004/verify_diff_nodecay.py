"""Fail-closed server gate. Its temporary optimizer steps are never resumed."""
import json
import os
import sys
from pathlib import Path

import torch
from mmcv import Config

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from opera.models import build_model
from opera.datasets.wifi_pose import WifiPoseDataset
from opera.models import tpami2026_scratch, tpami2026_diff_nodecay
from opera.models.tpami2026_diff_nodecay import PREFIX, validate_groups
from mmcv.runner import build_optimizer
from opera.models.transfer_support import (load_checkpoint_cpu, module_norms,
                                           PoseTransferOptimizerConstructor)


def main():
    torch.manual_seed(0)
    torch.set_num_threads(4)
    report_dir = ROOT / 'result/tpami2026_diff_nodecay_20261004/gates'
    report_dir.mkdir(parents=True, exist_ok=True)
    cfg = Config.fromfile(str(ROOT / 'configs/wifi/petr_wifi_tpami2026_diff_nodecay.py'))
    reference = Config.fromfile(str(ROOT / 'configs/wifi/petr_wifi_tpami2026_scratch.py'))
    assert cfg.model == reference.model and cfg.data.train == reference.data.train
    for field in ('lr_config', 'checkpoint_config', 'evaluation', 'seed', 'load_from', 'resume_from'):
        assert cfg[field] == reference[field], field
    old_init = json.loads((ROOT / 'result/tpami2026_scratch_20261004/initialization.json').read_text())
    assert cfg.model.transfer_checkpoint is None
    assert cfg.load_from is None and cfg.resume_from is None and not cfg.auto_resume
    calls = []
    original_load = torch.load
    def forbidden_load(*args, **kwargs):
        calls.append(str(args[0]) if args else 'load')
        raise AssertionError('Fresh initialization attempted checkpoint loading')
    torch.load = forbidden_load
    try:
        model = build_model(cfg.model)
        model.init_weights()
    finally:
        torch.load = original_load
    assert not calls
    assert model.initialization_report['checkpoint_loaded'] is False
    for key, norm in model.initialization_report['module_parameter_l2'].items():
        assert abs(norm - old_init['module_parameter_l2'][key]) < 1e-10, key
    assert all(torch.isfinite(x).all() for x in model.state_dict().values())
    from mmcv.runner.hooks.lr_updater import StepLrUpdaterHook
    from types import SimpleNamespace
    lr_hook = StepLrUpdaterHook(step=[450], gamma=0.1)
    assert lr_hook.get_lr(SimpleNamespace(epoch=449), 2e-5) == 2e-5
    assert abs(lr_hook.get_lr(SimpleNamespace(epoch=450), 2e-5) - 2e-6) < 1e-15
    model.eval()
    transformer = model.bbox_head.transformer
    assert len(transformer.encoder.layers) == 6
    assert len(transformer.decoder.layers) == 3
    assert len(transformer.refine_decoder.layers) == 3
    assert len(transformer.joint_differentiators) == 14
    attention_types = []
    for layer in transformer.refine_decoder.layers:
        assert tuple(layer.operation_order) == ('self_attn', 'norm', 'cross_attn', 'norm', 'ffn', 'norm')
        for att in layer.attentions:
            assert isinstance(att.attn, torch.nn.MultiheadAttention)
            assert att.attn.num_heads == 8 and att.attn.embed_dim == 256
            attention_types.append(type(att.attn).__module__ + '.' + type(att.attn).__name__)
    weights, biases = [], []
    for branch in transformer.joint_differentiators:
        assert isinstance(branch[1], torch.nn.LeakyReLU)
        for layer in branch:
            if isinstance(layer, torch.nn.Linear):
                weights.append(layer.weight.detach().flatten())
                biases.append(layer.bias.detach().flatten())
    w, b = torch.cat(weights), torch.cat(biases)
    assert 0.0009 < w.std().item() < 0.0011
    assert 0.0009 < b.std().item() < 0.0011
    for branch in model.bbox_head.refine_kpt_branches:
        assert torch.count_nonzero(branch[-1].weight) == 0
        assert torch.count_nonzero(branch[-1].bias) == 0
        assert branch[0].weight.std() > 0.01
    assert next(transformer.refine_decoder.parameters()).std() > 0.01

    dataset = object.__new__(WifiPoseDataset)
    dataset.data_root = str(ROOT / 'data/wifipose/test_data')
    dataset.filename_list = ['S11_01_308', 'S12_01_331', 'S13_07_304']
    samples = [dataset.get_item_single_frame(i) for i in range(3)]
    assert [len(x['gt_keypoints']) for x in samples] == [1, 2, 3]
    x = torch.stack([sample['img'] for sample in samples])
    with torch.no_grad():
        # Sparse matching across a batch must gather both identity and memory correctly.
        identities = torch.randn(2, 100, 256)
        poses = torch.randn(200, 42)
        weights_mask = torch.zeros_like(poses)
        selected = torch.tensor([0, 99, 100, 199])
        weights_mask[selected] = 1
        memory = torch.randn(180, 2, 256)
        captured = []
        forward = transformer.forward_refine

        def spy(mem, refs, images, ids, **kwargs):
            captured.append((refs.clone(), images.clone(), ids.clone()))
            return forward(mem, refs, images, ids, **kwargs)

        transformer.forward_refine = spy
        refined = model.bbox_head.forward_refine(memory, (poses, poses, weights_mask), None, identities)
        assert torch.equal(captured[-1][1], torch.tensor([0, 0, 1, 1]))
        assert torch.equal(captured[-1][2], identities.reshape(-1, 256)[selected])
        assert torch.equal(refined[-1], poses[selected].reshape(4, 14, 3))
        # Sorting by confidence must apply the identical permutation to identity/pose.
        # Avoid sigmoid saturation and tied scores in the strict-order fixture.
        scores = torch.linspace(-2, 2, 100).reshape(100, 1)
        model.bbox_head._get_bboxes_single(scores, poses[:100], memory[:, :1], identities[0])
        order = torch.arange(99, -1, -1)
        assert torch.equal(captured[-1][0], poses[:100][order])
        assert torch.equal(captured[-1][2], identities[0][order])
        transformer.forward_refine = forward
        queries = transformer.make_joint_queries(identities[0][:3])
        assert queries.shape == (3, 14, 256)
        residual = float((queries - identities[0][:3, None]).square().mean().sqrt())
        joint_spread = float((queries[:, 0] - queries[:, 1]).norm())
        assert 0 < residual < 0.01 and joint_spread > 0

    model.cuda().train()
    optimizer = build_optimizer(model, cfg.optimizer)
    groups = validate_groups(model, optimizer)
    assert len(optimizer.state) == 0
    assert groups[0]['weight_decay'] == 0 and groups[1]['weight_decay'] == 1e-4
    inputs = dict(img=x.cuda(), img_metas=[{}, {}, {}],
                  gt_bboxes=[s['gt_bboxes'].cuda() for s in samples],
                  gt_labels=[torch.tensor(s['gt_labels'], device='cuda') for s in samples],
                  gt_keypoints=[s['gt_keypoints'].cuda() for s in samples],
                  gt_areas=[s['gt_areas'].cuda() for s in samples])
    # First update opens the initially zero regression heads. Second backward
    # uses ONLY refinement losses to prove the new branch reaches pose identities.
    losses = model(return_loss=True, **inputs)
    loss = sum(losses.values())
    assert torch.isfinite(loss)
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1, error_if_nonfinite=True)
    before_diff = {n: p.detach().clone() for n, p in model.named_parameters() if n.startswith(PREFIX)}
    assert all(p.grad is not None and torch.count_nonzero(p.grad) == 0
               for n, p in model.named_parameters() if n.startswith(PREFIX))
    optimizer.step()
    assert all(torch.equal(before_diff[n], p) for n, p in model.named_parameters() if n.startswith(PREFIX))
    losses = model(return_loss=True, **inputs)
    optimizer.zero_grad()
    sum(v for k, v in losses.items() if 'loss_kpt_refine' in k).backward()
    grad_norms = module_norms(model, gradients=True)
    for name in ('differentiate', 'refine_attention', 'refine_regression', 'pose_decoder'):
        assert grad_norms[name] > 0, (name, grad_norms)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1, error_if_nonfinite=True)
    report = {'passed': True, 'optimizer_groups': groups, 'zero_gradient_diff_parameters_unchanged': True, 'initialization': model.initialization_report,
              'refine_layers': 3, 'vanilla_attention': attention_types,
              'differentiation_weight_std': w.std().item(), 'differentiation_bias_std': b.std().item(),
              'zero_regression_output_heads': True, 'checkpoint_calls': calls, 'step450_boundary_checked': True,
              'batch_person_indexing': True, 'score_sort_identity_alignment': True,
              'query_residual_rms': residual, 'query_joint_difference_l2': joint_spread,
              'refine_only_gradient_l2_after_one_discarded_step': grad_norms,
              'paper_choices': {'mlp_depth': 2, 'initialization_std': 0.001,
                                'not_author_published_hyperparameters': True}}
    (report_dir / 'unit_gate.json').write_text(json.dumps(report, indent=2))
    print('UNIT_GATE_PASS ' + json.dumps({k: v for k, v in report.items() if k not in ('initialization', 'optimizer_groups')}), flush=True)


if __name__ == '__main__':
    main()
