"""Contiguous-data fine-tuning adapters; no deployment/model/preprocess changes.

Import through ``custom_imports`` together with ``paired_training``. Set
``lr_config=None`` when using KinectValidationLrHook; it owns warmup and decay.
"""
from collections import OrderedDict
import json
import math
import os
from pathlib import Path
import time

import numpy as np
import torch
import torch.distributed as dist
from mmcv.runner import HOOKS, Hook
from mmdet.datasets.pipelines import Compose
from opera.datasets.builder import DATASETS
from opera.models.builder import DETECTORS
from opera.models.pose180.detector import PETR180
from opera.core.keypoint import bbox_kpt2result
from paired_training import PETR180Finetune


@DETECTORS.register_module()
class PETR180FastFinetune(PETR180Finetune):
    """Original inference path with the already-batched 180-query head.

    The original PETR detector asserted one input although PETR180Head.get_bboxes
    processes each batch member. No weights, candidate selection, or arithmetic
    is changed here; strict epoch99 initialization is inherited unchanged.
    """
    def simple_test(self, img, img_metas, rescale=False):
        bs, _, _, _, channel = img.shape
        if bs != len(img_metas):
            raise ValueError('Input and metadata batch sizes differ')
        x = img.reshape(bs, -1, channel)
        feat = self.head(x)
        results_list = self.bbox_head.simple_test(feat, img_metas, rescale=rescale)
        return [bbox_kpt2result(det_bboxes, det_labels, det_kpts,
                               self.bbox_head.num_classes)
                for det_bboxes, det_labels, det_kpts in results_list]


@DETECTORS.register_module()
class PETR180FastScratch(PETR180FastFinetune):
    """Same batched inference, but use the original guarded scratch initializer.

    The direct PETR180 call deliberately bypasses PETR180Finetune.init_weights.
    That original scratch branch forbids torch.load during initialization and
    records loaded=0, source=None and reinitialized='all_model_parameters'.
    """
    def __init__(self, *args, source_checkpoint=None, **kwargs):
        if source_checkpoint is not None:
            raise ValueError('Scratch comparison must not receive a checkpoint')
        super().__init__(*args, source_checkpoint=None, **kwargs)

    def init_weights(self):
        if self.source_checkpoint is not None:
            raise ValueError('Scratch initialization cannot load a checkpoint')
        return PETR180.init_weights(self)


def evenly_spaced_indices(length, maximum_samples=None):
    """Deterministic temporal sampling, with no duplicated sample indices."""
    if length < 1:
        raise ValueError('A nonempty finalized split is required')
    if maximum_samples is None:
        return np.arange(length, dtype=np.int64)
    if isinstance(maximum_samples, bool) or int(maximum_samples) != maximum_samples or maximum_samples < 1:
        raise ValueError('maximum_samples must be a positive integer or None')
    count = min(length, int(maximum_samples))
    return np.linspace(0, length - 1, count, dtype=np.int64)


@DATASETS.register_module()
class KinectWifiMemmapDataset(torch.utils.data.Dataset):
    """Read real preprocessed tokens and calibrated single-person labels.

    Each split has tokens.npy [N,180,60], keypoints.npy [N,P,14,3],
    and names.json (a JSON list in identical row order). P is 1..3. An optional
    person_counts.npy [N] supplies valid slots when official TRAIN labels are
    padded; absent counts mean every slot is valid. Validation subsampling
    changes only the in-memory view, never files or the reserved test split.
    """
    CLASSES = ('person',)

    def __init__(self, dataset_root, pipeline, mode, metrics_path=None,
                 maximum_samples=None, test_mode=False, **kwargs):
        self.data_root = str(Path(dataset_root).resolve())
        self.mode = mode
        self.test_mode = test_mode
        self.metrics_path = metrics_path
        self.pipeline = Compose(pipeline)
        root = Path(self.data_root)
        names = json.loads((root / 'names.json').read_text(encoding='utf-8-sig'))
        if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
            raise ValueError('names.json must be a nonempty list of real sample identities')
        if len(set(names)) != len(names):
            raise ValueError('Duplicate row identities in the finalized split')
        self.full_count = len(names)
        self.row_indices = evenly_spaced_indices(self.full_count, maximum_samples)
        self.filename_list = [names[int(i)] for i in self.row_indices]
        self.flag = np.zeros(len(self.filename_list), dtype=np.uint8)
        self._tokens = self._poses = self._person_counts = None
        self._pid = None
        self._open_arrays()

    def _open_arrays(self):
        if self._pid == os.getpid() and self._tokens is not None:
            return
        root = Path(self.data_root)
        tokens = np.load(root / 'tokens.npy', mmap_mode='r', allow_pickle=False)
        poses = np.load(root / 'keypoints.npy', mmap_mode='r', allow_pickle=False)
        if (tokens.shape != (self.full_count, 180, 60) or poses.ndim != 4 or
                poses.shape[0] != self.full_count or poses.shape[2:] != (14, 3) or not 1 <= poses.shape[1] <= 3):
            raise ValueError('Contiguous input/label shape differs from the original 14-joint contract')
        if tokens.dtype != np.dtype('float32') or poses.dtype != np.dtype('float32'):
            raise ValueError('Contiguous arrays must retain float32 token/label values')
        count_path = root / 'person_counts.npy'
        counts = np.load(count_path, mmap_mode='r', allow_pickle=False) if count_path.exists() else None
        if counts is not None and (counts.shape != (self.full_count,) or counts.dtype.kind not in 'iu' or
                                   np.any(counts < 1) or np.any(counts > poses.shape[1])):
            raise ValueError('Invalid actual person counts for padded official labels')
        self._tokens, self._poses, self._person_counts, self._pid = tokens, poses, counts, os.getpid()

    def __getstate__(self):
        state = dict(self.__dict__)
        state['_tokens'] = state['_poses'] = state['_person_counts'] = state['_pid'] = None
        return state

    def __len__(self):
        return len(self.filename_list)

    def get_item_single_frame(self, index):
        self._open_arrays()
        row = int(self.row_indices[index])
        # Copies avoid exposing a read-only mmap to mutable pipeline/Torch code.
        tokens = np.array(self._tokens[row], copy=True)
        count = int(self._person_counts[row]) if self._person_counts is not None else self._poses.shape[1]
        gt = np.array(self._poses[row, :count], copy=True)
        if not np.isfinite(tokens).all() or not np.isfinite(gt).all():
            raise ValueError('Non-finite actual sample: ' + self.filename_list[index])
        return dict(img=torch.from_numpy(tokens.reshape(3, 3, 20, 60)),
                    gt_keypoints=torch.from_numpy(gt), gt_labels=np.zeros(count, dtype=np.int64),
                    gt_bboxes=torch.tensor([]), gt_areas=torch.tensor([]),
                    img_name=self.filename_list[index])

    def __getitem__(self, index):
        return self.pipeline(self.get_item_single_frame(index))

    def evaluate(self, results, **kwargs):
        """Original best-of-180 error plus actual highest-score single-person error.

        For one real person the original greedy assignment selects the candidate
        with the smallest mean joint Euclidean distance. This vectorized version
        computes that same metric; it does not use root alignment or Procrustes.
        """
        if len(results) != len(self):
            raise ValueError('Incomplete validation view')
        self._open_arrays()
        best_errors, top1_errors, count_errors, counts, threshold_errors = [], [], [], [], []
        for index, (boxes, keypoints) in enumerate(results):
            row = int(self.row_indices[index])
            person_count = int(self._person_counts[row]) if self._person_counts is not None else self._poses.shape[1]
            if person_count != 1:
                raise ValueError('Use the original official evaluator for multi-person evaluation; this Top1 metric is for local single-person validation')
            real = np.asarray(self._poses[row][0], dtype=np.float32)
            prediction = np.asarray(keypoints[0], dtype=np.float32)
            scores = np.asarray(boxes[0], dtype=np.float32)[:, -1]
            if prediction.shape != (180, 14, 3) or scores.shape != (180,):
                raise ValueError('Validation must preserve all 180 candidate identities')
            if not np.isfinite(prediction).all() or not np.isfinite(scores).all() or not np.isfinite(real).all():
                raise ValueError('Non-finite validation prediction/reference')
            difference = prediction - real[None]
            joint_distances = np.linalg.norm(difference, axis=-1)
            distances = joint_distances.mean(axis=-1)
            best = int(np.argmin(distances))
            top1 = int(np.argmax(scores))
            best_errors.append([float(distances[best]) * 1000] +
                               (np.abs(difference[best]).mean(axis=0) * 1000).tolist())
            top1_errors.append(float(distances[top1]) * 1000)
            selected = scores > .2
            count = int(selected.sum())
            counts.append(count)
            count_errors.append(abs(count - 1))
            if count:
                threshold_errors.append(float(distances[selected].min()) * 1000)
        means = np.mean(best_errors, axis=0)
        metrics = OrderedDict(zip(('mpjpe', 'mpjpeh', 'mpjpev', 'mpjped'), means.tolist()))
        metrics.update(mpjpe_1_people=float(means[0]), top1_mpjpe=float(np.mean(top1_errors)),
                       candidate_count=180, count_mae_at_0_2=float(np.mean(count_errors)),
                       mean_selected_at_0_2=float(np.mean(counts)))
        if threshold_errors:
            metrics['matched_mpjpe_at_0_2'] = float(np.mean(threshold_errors))
        if self.metrics_path:
            record = dict(time=time.time(), frames=len(self), full_split_frames=self.full_count,
                          fixed_subset=len(self) != self.full_count, metrics=metrics)
            with Path(self.metrics_path).open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, allow_nan=False) + '\n')
        return metrics


class ValidationDecayState:
    """Pure scheduler state: all decisions depend on observed validation error."""
    def __init__(self, factor=.3, improvement_fraction=.2, patience=2,
                 min_relative_improvement=.005, cooldown=1, max_reductions=3,
                 baseline_metric=None):
        if not 0 < factor < 1 or not 0 < improvement_fraction < 1:
            raise ValueError('Invalid decay/improvement fraction')
        if patience < 1 or cooldown < 0 or max_reductions < 1:
            raise ValueError('Invalid bounded scheduler budget')
        if not 0 <= min_relative_improvement < 1:
            raise ValueError('Invalid minimum relative improvement')
        self.factor = factor
        self.improvement_fraction = improvement_fraction
        self.patience = int(patience)
        self.min_relative_improvement = min_relative_improvement
        self.cooldown = int(cooldown)
        self.max_reductions = int(max_reductions)
        self.baseline = None
        self.best = None
        self.bad_epochs = 0
        self.remaining_cooldown = 0
        self.reductions = 0
        self.improvement_reduction_used = False
        if baseline_metric is not None:
            self.set_baseline(baseline_metric)

    def set_baseline(self, value):
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError('Baseline validation error must be finite and nonnegative')
        self.baseline = self.best = value

    def observe(self, value):
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError('Validation error must be finite and nonnegative')
        if self.baseline is None:
            self.set_baseline(value)
            return None
        improved = value < self.best * (1 - self.min_relative_improvement)
        if improved:
            self.best = value
            self.bad_epochs = 0
        elif self.remaining_cooldown == 0:
            self.bad_epochs += 1
        if self.remaining_cooldown:
            self.remaining_cooldown -= 1
            return None
        if self.reductions >= self.max_reductions:
            return None
        reason = None
        if not self.improvement_reduction_used and self.baseline > 0 and value <= self.baseline * (1 - self.improvement_fraction):
            self.improvement_reduction_used = True
            reason = 'validation_error_reduced_by_%g_percent' % (100 * self.improvement_fraction)
        elif self.bad_epochs >= self.patience:
            reason = 'validation_plateau_%d_evaluations' % self.bad_epochs
        if reason:
            self.reductions += 1
            self.bad_epochs = 0
            self.remaining_cooldown = self.cooldown
        return reason


def latest_metric(path, metric):
    """Read a JSON baseline or the last complete JSONL evaluation record."""
    text = Path(path).read_text(encoding='utf-8-sig').strip()
    try:
        record = json.loads(text)
    except json.JSONDecodeError:
        record = json.loads(text.splitlines()[-1])
    value = float(record.get('metrics', record)[metric])
    if not math.isfinite(value) or value < 0:
        raise ValueError('Invalid validation metric in ' + str(path))
    return value


@HOOKS.register_module()
class KinectValidationLrHook(Hook):
    """Use priority='VERY_LOW' so this runs after the native LOW EvalHook.

    All ranks enter the same broadcast after validation. Only rank zero reads
    metrics files; all ranks apply the same observation and LR change. A finite
    initial-model validation may be supplied as baseline_path or baseline_metric.
    """
    def __init__(self, metrics_path, metric='top1_mpjpe', factor=.3,
                 improvement_fraction=.2, patience=2, min_lr=2e-7,
                 min_relative_improvement=.005, cooldown=1, max_reductions=3,
                 warmup_iters=100, warmup_ratio=.1, baseline_metric=None,
                 baseline_path=None):
        if baseline_metric is not None and baseline_path is not None:
            raise ValueError('Use one explicit baseline source')
        if warmup_iters < 0 or not 0 < warmup_ratio <= 1 or min_lr < 0:
            raise ValueError('Invalid warmup/minimum learning rate')
        self.metrics_path, self.metric = str(metrics_path), metric
        self.baseline_path = baseline_path
        self.state = ValidationDecayState(factor, improvement_fraction, patience,
            min_relative_improvement, cooldown, max_reductions, baseline_metric)
        self.min_lr = min_lr
        self.warmup_iters, self.warmup_ratio = int(warmup_iters), warmup_ratio
        self.offset = 0
        self.base_lrs = []

    def _distributed_value(self, runner, callback):
        message = None
        if runner.rank == 0:
            try:
                message = dict(value=callback(), error=None)
            except Exception as error:
                message = dict(value=None, error=type(error).__name__ + ': ' + str(error))
        if dist.is_available() and dist.is_initialized():
            messages = [message]
            dist.broadcast_object_list(messages, src=0)
            message = messages[0]
        if message['error']:
            raise RuntimeError(message['error'])
        return message['value']

    def before_run(self, runner):
        from mmcv.runner.hooks.lr_updater import LrUpdaterHook
        if any(isinstance(h, LrUpdaterHook) for h in runner.hooks):
            raise ValueError('Set lr_config=None; a second LR hook would overwrite validation-driven decay')
        if isinstance(runner.optimizer, dict):
            raise ValueError('This adapter expects the existing single AdamW optimizer')
        self.base_lrs = [float(g['lr']) for g in runner.optimizer.param_groups]
        if not self.base_lrs or min(self.base_lrs) <= 0:
            raise ValueError('Positive initial learning rates required')
        def initialize():
            self.offset = Path(self.metrics_path).stat().st_size if Path(self.metrics_path).exists() else 0
            return latest_metric(self.baseline_path, self.metric) if self.baseline_path else None
        baseline = self._distributed_value(runner, initialize)
        if baseline is not None:
            self.state.set_baseline(baseline)
        if runner.rank == 0:
            self._log(runner, dict(event='configured', baseline=self.state.baseline,
                baseline_source=str(self.baseline_path) if self.baseline_path else
                    ('explicit_value' if self.state.baseline is not None else 'first_training_epoch_validation'),
                initial_lrs=self.base_lrs, warmup_iters=self.warmup_iters))

    def before_train_iter(self, runner):
        if self.warmup_iters and runner.iter < self.warmup_iters:
            ratio = self.warmup_ratio + (1 - self.warmup_ratio) * min(1., (runner.iter + 1) / self.warmup_iters)
            for group, base in zip(runner.optimizer.param_groups, self.base_lrs):
                group['lr'] = base * ratio

    def _read_new_metric(self):
        path = Path(self.metrics_path)
        if not path.exists():
            return None
        with path.open('rb') as stream:
            stream.seek(self.offset)
            payload = stream.read()
            if not payload:
                return None
            if not payload.endswith(b'\n'):
                raise ValueError('Validation metrics record is incomplete')
            self.offset = stream.tell()
        record = json.loads(payload.decode('utf-8').splitlines()[-1])
        return dict(metric=float(record['metrics'][self.metric]), frames=record['frames'],
                    fixed_subset=bool(record.get('fixed_subset', False)), time=record['time'])

    def after_train_epoch(self, runner):
        observation = self._distributed_value(runner, self._read_new_metric)
        if observation is None:
            return
        old = [float(g['lr']) for g in runner.optimizer.param_groups]
        reason = self.state.observe(observation['metric'])
        if reason:
            for group in runner.optimizer.param_groups:
                group['lr'] = max(self.min_lr, float(group['lr']) * self.state.factor)
        new = [float(g['lr']) for g in runner.optimizer.param_groups]
        if runner.rank == 0:
            self._log(runner, dict(event='validation', epoch=runner.epoch + 1,
                observation=observation, baseline=self.state.baseline, best=self.state.best,
                old_lrs=old, new_lrs=new, reason=reason, reductions=self.state.reductions))

    def _log(self, runner, value):
        value.update(time=time.time(), metric_name=self.metric)
        with (Path(runner.work_dir) / 'learning-rate-decisions.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value, allow_nan=False) + '\n')


@HOOKS.register_module()
class KinectWallBudgetHook(Hook):
    """Finish at an epoch boundary and reserve time for held-out evaluation."""
    def __init__(self,seconds=4800):
        self.seconds=float(seconds)
        if not 60<=self.seconds<=7200:raise ValueError('Finite training budget required')
    def before_run(self,runner):self.started=time.monotonic()
    def before_train_epoch(self,runner):self.epoch_started=time.monotonic()
    def after_train_epoch(self,runner):
        elapsed=time.monotonic()-self.started;duration=time.monotonic()-self.epoch_started
        if elapsed+duration*1.15>=self.seconds:
            runner._max_epochs=runner.epoch+1
            if runner.rank==0:
                (Path(runner.work_dir)/'wall-budget-stop.json').write_text(json.dumps(dict(
                    completed_epochs=runner.epoch+1,elapsed_seconds=elapsed,last_epoch_seconds=duration,
                    budget_seconds=self.seconds,reason='Next epoch could consume reserved evaluation time'),indent=2)+'\n')
