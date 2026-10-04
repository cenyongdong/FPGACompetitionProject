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
from opera.models import tpami2026_transfer
from opera.models.transfer_support import (load_checkpoint_cpu, module_norms,
                                           PoseTransferOptimizerConstructor)


def main():
    torch.manual_seed(0)
    torch.set_num_threads(4)
    report_dir = ROOT / 'result/tpami2026_transfer_20261003/gates'
    report_dir.mkdir(parents=True, exist_ok=True)
    cfg = Config.fromfile(str(ROOT / 'configs/wifi/petr_wifi_tpami2026_transfer.py'))
    model = build_model(cfg.model)
    model.init_weights()
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

    baseline_cfg = Config.fromfile(str(ROOT / 'result/code_faithful/petr_wifi.py'))
    baseline_cfg.model.backbone.init_cfg = None
    baseline = build_model(baseline_cfg.model)
    baseline.load_state_dict(load_checkpoint_cpu(ROOT / cfg.model.transfer_checkpoint)['state_dict'], strict=True)
    baseline.eval()
    dataset = object.__new__(WifiPoseDataset)
    dataset.data_root = str(ROOT / 'data/wifipose/test_data')
    dataset.filename_list = ['S11_01_308', 'S12_01_331', 'S13_07_304']
    samples = [dataset.get_item_single_frame(i) for i in range(3)]
    assert [len(x['gt_keypoints']) for x in samples] == [1, 2, 3]
    x = torch.stack([s['img'] for s in samples])
    with torch.no_grad():
        saved_ste = model.head.ste.clone()
        model.head.ste.zero_()
        old = baseline.bbox_head(baseline.head(x.reshape(3, 180, 60)), [{}, {}, {}])
        new = model.bbox_head(model.head(x.reshape(3, 180, 60)), [{}, {}, {}])
        max_error = max((a - b).abs().max().item() for a, b in zip(old[:4], new[:4]))
        assert max_error == 0, max_error
        model.head.ste.copy_(saved_ste)

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

    del baseline, old, new
    model.cuda().train()
    optimizer = PoseTransferOptimizerConstructor(dict(type='AdamW', lr=2e-5,
                                                      weight_decay=1e-4))(model)
    assert len(optimizer.state) == 0
    for group in optimizer.param_groups:
        assert group['lr'] == (2e-6 if group['transferred'] else 2e-5)
        if 'joint_differentiators' in group['parameter_name']:
            assert group['weight_decay'] == 0
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
    optimizer.step()
    losses = model(return_loss=True, **inputs)
    optimizer.zero_grad()
    sum(v for k, v in losses.items() if 'loss_kpt_refine' in k).backward()
    grad_norms = module_norms(model, gradients=True)
    for name in ('differentiate', 'refine_attention', 'refine_regression', 'pose_decoder'):
        assert grad_norms[name] > 0, (name, grad_norms)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1, error_if_nonfinite=True)
    report = {'passed': True, 'migration': model.transfer_report,
              'refine_layers': 3, 'vanilla_attention': attention_types,
              'differentiation_weight_std': w.std().item(), 'differentiation_bias_std': b.std().item(),
              'zero_regression_output_heads': True, 'coarse_migration_max_error_ste_off': max_error,
              'batch_person_indexing': True, 'score_sort_identity_alignment': True,
              'query_residual_rms': residual, 'query_joint_difference_l2': joint_spread,
              'refine_only_gradient_l2_after_one_discarded_step': grad_norms,
              'paper_choices': {'mlp_depth': 2, 'initialization_std': 0.001,
                                'not_author_published_hyperparameters': True}}
    (report_dir / 'unit_gate.json').write_text(json.dumps(report, indent=2))
    print('UNIT_GATE_PASS ' + json.dumps({k: v for k, v in report.items() if k != 'migration'}), flush=True)


if __name__ == '__main__':
    main()
