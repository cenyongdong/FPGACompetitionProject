"""Offline contract tests: no sensors, remote host, training, or GPU work."""
import json
from pathlib import Path
import tempfile
import types
import sys
import unittest
from unittest import mock

import numpy as np
import torch

# The local capture Python intentionally lacks MMCV. Stub registration/pipelines
# only; all array reads, scheduler decisions, Torch tensors and metrics are real.
class Registry:
    def register_module(self):
        return lambda cls: cls


class StubPETR180:
    def __init__(self, source_checkpoint=None, **kwargs):
        self.source_checkpoint = source_checkpoint
        self.migration_report = None

    def init_weights(self):
        self.migration_report = dict(source=None, loaded=0, reinitialized='all_model_parameters')


class StubFinetune(StubPETR180):
    def init_weights(self):
        raise AssertionError('Scratch must bypass the fine-tuning initializer')

modules = {name: types.ModuleType(name) for name in (
    'mmcv', 'mmcv.runner', 'mmcv.runner.hooks', 'mmcv.runner.hooks.lr_updater',
    'mmdet', 'mmdet.datasets', 'mmdet.datasets.pipelines',
    'opera', 'opera.datasets', 'opera.datasets.builder',
    'opera.models', 'opera.models.builder', 'opera.core', 'opera.core.keypoint',
    'opera.models.pose180', 'opera.models.pose180.detector', 'paired_training')}
modules['mmcv.runner'].HOOKS = Registry()
modules['mmcv.runner'].Hook = object
modules['mmcv.runner.hooks.lr_updater'].LrUpdaterHook = type('LrUpdaterHook', (), {})
modules['mmdet.datasets.pipelines'].Compose = lambda pipeline: (lambda value: value)
modules['opera.datasets.builder'].DATASETS = Registry()
modules['opera.models.builder'].DETECTORS = Registry()
modules['opera.core.keypoint'].bbox_kpt2result = lambda boxes, labels, poses, classes: (boxes, poses)
modules['opera.models.pose180.detector'].PETR180 = StubPETR180
modules['paired_training'].PETR180Finetune = StubFinetune
with mock.patch.dict(sys.modules, modules):
    import fast_training as ft


def fixture(root, count=5):
    tokens = np.arange(count * 180 * 60, dtype=np.float32).reshape(count, 180, 60) / 100
    poses = np.zeros((count, 1, 14, 3), dtype=np.float32)
    poses[:, :, :, 0] = np.arange(count)[:, None, None]
    np.save(root / 'tokens.npy', tokens)
    np.save(root / 'keypoints.npy', poses)
    (root / 'names.json').write_text(json.dumps(['sample_%d' % i for i in range(count)]))
    return tokens, poses


class FastTraining(unittest.TestCase):
    def test_scratch_uses_original_initializer_not_finetune(self):
        model = ft.PETR180FastScratch(source_checkpoint=None)
        model.init_weights()
        self.assertEqual(model.migration_report,
            dict(source=None, loaded=0, reinitialized='all_model_parameters'))
        self.assertIs(model.simple_test.__func__, ft.PETR180FastFinetune.simple_test)
        with self.assertRaisesRegex(ValueError, 'must not receive'):
            ft.PETR180FastScratch(source_checkpoint='epoch99.pth')
        model.source_checkpoint = 'epoch99.pth'
        with self.assertRaisesRegex(ValueError, 'cannot load'):
            model.init_weights()

    def test_contiguous_row_identity_and_nonmutating_subset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tokens, poses = fixture(root)
            ds = ft.KinectWifiMemmapDataset(root, [], 'test', maximum_samples=3)
            self.assertEqual(ds.filename_list, ['sample_0', 'sample_2', 'sample_4'])
            self.assertEqual(ds.full_count, 5)
            row = ds.get_item_single_frame(1)
            np.testing.assert_array_equal(row['img'].numpy().reshape(180, 60), tokens[2])
            np.testing.assert_array_equal(row['gt_keypoints'].numpy(), poses[2])
            row['img'][0, 0, 0, 0] = -99
            np.testing.assert_array_equal(np.load(root / 'tokens.npy'), tokens)
            state = ds.__getstate__()
            self.assertIsNone(state['_tokens'])
            self.assertIsNone(state['_poses'])
            with self.assertRaises(ValueError):
                ft.evenly_spaced_indices(10, 0)
            np.testing.assert_array_equal(ft.evenly_spaced_indices(3, 10), [0, 1, 2])
            ds._tokens._mmap.close()
            ds._poses._mmap.close()

    def test_metrics_distinguish_actual_top1_from_best_of_180(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root, 1)
            ds = ft.KinectWifiMemmapDataset(root, [], 'test', metrics_path=root / 'metrics.jsonl')
            prediction = np.zeros((180, 14, 3), dtype=np.float32)
            prediction[:, :, 0] = .5
            prediction[7, :, 0] = .1
            prediction[3, :, 0] = .2
            boxes = np.zeros((180, 5), dtype=np.float32)
            boxes[3, -1] = .9
            boxes[7, -1] = .3
            result = ds.evaluate([([boxes], [prediction])])
            self.assertAlmostEqual(result['mpjpe'], 100, places=3)
            self.assertAlmostEqual(result['top1_mpjpe'], 200, places=3)
            self.assertEqual(result['count_mae_at_0_2'], 1)
            self.assertAlmostEqual(result['matched_mpjpe_at_0_2'], 100, places=3)
            self.assertAlmostEqual(ft.latest_metric(root / 'metrics.jsonl', 'top1_mpjpe'), 200, places=3)
            self.assertFalse(json.loads((root / 'metrics.jsonl').read_text())['fixed_subset'])
            ds._tokens._mmap.close()
            ds._poses._mmap.close()

    def test_official_multiperson_padding_is_not_a_person(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root, 3)
            poses = np.full((3, 3, 14, 3), np.nan, dtype=np.float32)
            for i in range(3):
                poses[i, :i + 1] = i + 1
            np.save(root / 'keypoints.npy', poses)
            np.save(root / 'person_counts.npy', np.array([1, 2, 3], dtype=np.uint8))
            ds = ft.KinectWifiMemmapDataset(root, [], 'train')
            row = ds.get_item_single_frame(1)
            self.assertEqual(tuple(row['gt_keypoints'].shape), (2, 14, 3))
            self.assertEqual(tuple(row['gt_labels'].shape), (2,))
            np.testing.assert_array_equal(row['gt_keypoints'].numpy(), poses[1, :2])
            self.assertEqual(tuple(ds.get_item_single_frame(2)['gt_keypoints'].shape), (3, 14, 3))
            ds._tokens._mmap.close()
            ds._poses._mmap.close()
            ds._person_counts._mmap.close()

    def test_relative_improvement_then_plateau_and_budget(self):
        state = ft.ValidationDecayState(baseline_metric=100, max_reductions=2)
        self.assertIsNone(state.observe(90))
        self.assertEqual(state.observe(79), 'validation_error_reduced_by_20_percent')
        self.assertIsNone(state.observe(78))  # Cooldown still accepts a new best.
        self.assertIsNone(state.observe(78))
        self.assertEqual(state.observe(78), 'validation_plateau_2_evaluations')
        for _ in range(8):
            self.assertIsNone(state.observe(78))
        self.assertEqual(state.reductions, 2)
        with self.assertRaises(ValueError):
            state.observe(float('nan'))

    def test_first_observation_is_not_fabricated_pretraining_baseline(self):
        state = ft.ValidationDecayState()
        self.assertIsNone(state.observe(500))
        self.assertEqual(state.baseline, 500)
        self.assertEqual(state.observe(400), 'validation_error_reduced_by_20_percent')

    def test_hook_warmup_new_record_and_lr_floor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'metrics.jsonl'
            hook = ft.KinectValidationLrHook(path, baseline_metric=100, warmup_iters=100, min_lr=2e-7)
            optimizer = types.SimpleNamespace(param_groups=[dict(lr=1e-5), dict(lr=3e-7)])
            runner = types.SimpleNamespace(rank=0, optimizer=optimizer, hooks=[hook], work_dir=str(root), iter=0, epoch=0)
            with mock.patch.dict(sys.modules, modules):
                hook.before_run(runner)
            hook.before_train_iter(runner)
            self.assertAlmostEqual(optimizer.param_groups[0]['lr'], 1.09e-6)
            runner.iter = 99
            hook.before_train_iter(runner)
            self.assertEqual(optimizer.param_groups[0]['lr'], 1e-5)
            path.write_text(json.dumps(dict(time=1, frames=1200, fixed_subset=True, metrics=dict(top1_mpjpe=75))) + '\n')
            hook.after_train_epoch(runner)
            self.assertAlmostEqual(optimizer.param_groups[0]['lr'], 3e-6)
            self.assertEqual(optimizer.param_groups[1]['lr'], 2e-7)
            hook.after_train_epoch(runner)  # Same old evaluation must not be used twice.
            self.assertEqual(hook.state.reductions, 1)
            rows = [json.loads(line) for line in (root / 'learning-rate-decisions.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]['observation']['frames'], 1200)

    def test_nonzero_rank_never_reads_metric_and_receives_error(self):
        hook = ft.KinectValidationLrHook('unused.jsonl')
        runner = types.SimpleNamespace(rank=1)
        callback = mock.Mock(side_effect=AssertionError('Rank one must not read files'))
        def deliver(messages, src):
            messages[0] = dict(value=123, error=None)
        with mock.patch.object(ft.dist, 'is_available', return_value=True), mock.patch.object(ft.dist, 'is_initialized', return_value=True), mock.patch.object(ft.dist, 'broadcast_object_list', side_effect=deliver):
            self.assertEqual(hook._distributed_value(runner, callback), 123)
        callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
