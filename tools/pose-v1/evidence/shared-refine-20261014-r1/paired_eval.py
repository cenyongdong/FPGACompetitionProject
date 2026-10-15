"""Bounded full-test comparison; fixed epoch442, both TopK operations retained."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback
import types

os.environ.setdefault('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', 'python')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
ROOT = Path('/public/cyd/Person-in-WiFi-3D-repo')
sys.path.insert(0, str(ROOT))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    temp = Path(str(path) + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def extract(path, class_name, method_name, globals_dict):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    namespace = dict(globals_dict)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[method_name]


def method_ast(path, cls, method):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return ast.dump(next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == method))


def main():
    import numpy as np
    import torch
    import mmcv
    from mmcv import Config
    from mmcv.runner import load_checkpoint
    from mmdet.utils import build_dp, compat_cfg, setup_multi_processes
    from opera.datasets import build_dataset, build_dataloader
    from opera.models import build_model
    import opera.models.utils.transformer as transformer_module
    import opera.models.dense_heads.petr_head as head_module

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'result' and out.is_dir()
    assert not (out / 'preflight.json').exists(), 'Never reuse an evaluation run'
    os.chdir(ROOT)
    started = time.monotonic()
    budget = 1800
    atol = 1e-5  # model coordinates; maximum 0.01mm per coordinate, not a deployment gate
    metric_limit_mm = 0.01
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)

    checkpoint_path = ROOT / 'result/code_faithful/best_mpjpe_epoch_442.pth'
    config_path = ROOT / 'result/code_faithful/petr_wifi.py'
    source_path = ROOT / 'opera/models/utils/transformer.py'
    head_path = ROOT / 'opera/models/dense_heads/petr_head.py'
    pins = {
        str(checkpoint_path.relative_to(ROOT)): '6493e2250b83aef59ce4825e15d2d0043a59490275f75933f9a59867867d3221',
        str(config_path.relative_to(ROOT)): '9851f018164c56736c246246a199c4d5eba0d26c1bc0a98dcb40c6bf9059229c',
        'data/wifipose/test_data/test_data_list.txt': '989b5cf38b96e2f41986933feb7fb9dc4ff243ee8b550f272b97a0759ac35a18',
        'opera/datasets/wifi_pose.py': '52b603525b351b25e16f00237c787ea65d6957dbed0535899007d3fcfaafdb31',
        'opera/models/detectors/petr.py': 'aad242f588c1f45ea7cc51e286a5714e6da44b9012b5225c258a2b5d5e4fec18',
    }
    for name, expected in pins.items():
        assert sha(ROOT / name) == expected, 'Identity changed: ' + name
    assert sha(out / 'transformer.before.py') == '8952d85edee1470c669943ddeec3655b71cb868ca834ea9ab8fe75183ff478e2'
    assert sha(out / 'petr_head.before.py') == '75bc37c0cc402837cb9638d42df6067c5e4dd29c9a1647130ccacb51ce704ad7'
    for name, path in [('transformer', source_path), ('petr_head', head_path)]:
        assert path.read_bytes() == (out / (name + '.after.py')).read_bytes()
    assert Path(transformer_module.__file__).resolve() == source_path
    assert Path(head_module.__file__).resolve() == head_path
    # These unchanged methods contain the first and second TopK operations.
    for name, cls, method in [('transformer', 'PETRTransformer', 'forward'),
                              ('petr_head', 'PETRHead', '_get_bboxes_single')]:
        assert method_ast(out / (name + '.before.py'), cls, method) == method_ast(out / (name + '.after.py'), cls, method)

    cfg = compat_cfg(Config.fromfile(str(config_path)))
    cfg.data.test.test_mode = True
    cfg.model.train_cfg = None
    cfg.model.backbone.init_cfg = None
    cfg.opencv_num_threads = 0
    setup_multi_processes(cfg)
    dataset = build_dataset(cfg.data.test)
    assert len(dataset) == 7824
    assert cfg.model.bbox_head.num_query == 100
    assert cfg.model.test_cfg.max_per_img == 100
    assert cfg.model.bbox_head.transformer.refine_decoder.num_layers == 2
    assert cfg.model.bbox_head.num_keypoints == 14
    loader = build_dataloader(dataset, samples_per_gpu=1, workers_per_gpu=2,
                              dist=False, shuffle=False, seed=0, persistent_workers=False)
    model = build_model(cfg.model, test_cfg=cfg.get('test_cfg'))
    checkpoint = load_checkpoint(model, str(checkpoint_path), map_location='cpu', strict=True)
    assert checkpoint['meta']['epoch'] == 442
    model.CLASSES = checkpoint.get('meta', {}).get('CLASSES', dataset.CLASSES)
    model = build_dp(model, 'cuda', device_ids=[0])
    model.eval()
    head = model.module.bbox_head
    transformer = head.transformer
    decoder = transformer.refine_decoder
    specs = [(decoder, 'forward', 'transformer', 'PetrRefineTransformerDecoder', transformer_module),
             (transformer, 'forward_refine', 'transformer', 'PETRTransformer', transformer_module),
             (head, 'forward_refine', 'petr_head', 'PETRHead', head_module)]
    methods = {'before': [], 'after': []}
    for obj, name, file_name, cls, module in specs:
        methods['before'].append((obj, name, extract(out / (file_name + '.before.py'), cls, name, vars(module))))
        methods['after'].append((obj, name, getattr(obj, name).__func__))

    def select(mode):
        for obj, name, method in methods[mode]:
            setattr(obj, name, types.MethodType(method, obj))

    def weights_digest():
        h = hashlib.sha256()
        for name, value in sorted(model.module.state_dict().items()):
            h.update(name.encode())
            h.update(value.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()

    original_weights = weights_digest()
    cfg.dump(str(out / 'resolved_config.py'))
    preflight = dict(status='ready', cwd=str(ROOT), python=sys.executable,
                     torch=torch.__version__, mmcv=mmcv.__version__,
                     GPU=os.environ.get('CUDA_VISIBLE_DEVICES'), test_frames=len(dataset),
                     source_sha256={p.name:sha(p) for p in out.glob('*.before.py')},
                     after_sha256={p.name:sha(p) for p in out.glob('*.after.py')}, pins=pins,
                     budget_seconds=budget, batch=1, workers=2, dtype='FP32',
                     pretrained_download=False, training_update=False, topk_retained=2,
                     metric='unchanged WifiPoseDataset.calc_mpjpe; greedy all100 candidates, frame mean',
                     input_pairing='same preprocessed batch; same RNG; alternating before/after order',
                     precision_rule=dict(scores_bitwise=True, coordinate_abs_limit=atol,
                                         mean_mpjpe_abs_limit_mm=metric_limit_mm),
                     stop_rule='timeout/OOM/nonfinite/identity drift/shape mismatch/score mismatch/coordinate bound',
                     timing='CUDA synchronized whole-model wall time and decoder CUDA events; includes probes; no board timing')
    save_json(out / 'preflight.json', preflight)

    # Synthetic guards use the real loaded modules and weights, without an optimizer.
    rng_cpu, rng_gpu = torch.get_rng_state(), torch.cuda.get_rng_state_all()
    memory = torch.randn(180, 1, 256, device='cuda')
    coarse = torch.randn(100, 42, device='cuda')
    targets = torch.randn_like(coarse)
    weights = torch.zeros_like(coarse)
    weights[:3] = 1
    training_results = {}
    head.train()
    for mode in ('before', 'after'):
        select(mode)
        head.zero_grad(set_to_none=True)
        torch.set_rng_state(rng_cpu)
        torch.cuda.set_rng_state_all(rng_gpu)
        mem = memory.detach().clone().requires_grad_(True)
        losses = head.forward_refine(mem, (coarse, targets, weights), {}, None)
        total = sum(losses.values())
        total.backward()
        grads = {name:p.grad.detach().cpu().numpy().copy()
                 for name,p in head.named_parameters() if p.grad is not None}
        grads['input_memory'] = mem.grad.detach().cpu().numpy().copy()
        training_results[mode] = ({k:float(v) for k,v in losses.items()}, grads)
    assert training_results['before'][0] == training_results['after'][0]
    assert training_results['before'][1].keys() == training_results['after'][1].keys()
    assert all(training_results['before'][1][k].tobytes() == training_results['after'][1][k].tobytes()
               for k in training_results['before'][1]), 'Training gradient changed'
    gradient_count = sum(v.size for v in training_results['before'][1].values())
    head.zero_grad(set_to_none=True)
    model.eval()
    del training_results
    fallback_results = {}
    for case in ('multi_image', 'extra_kwargs'):
        batch = 2 if case == 'multi_image' else 1
        mem = torch.randn(180, batch, 256, device='cuda')
        refs = torch.randn(6, 42, device='cuda')
        indices = torch.arange(6, device='cuda') % batch
        results = {}
        for mode in ('before', 'after'):
            select(mode)
            with torch.no_grad():
                values = transformer.forward_refine(mem, refs, indices, head.refine_kpt_branches,
                          **({'key_padding_mask':None} if case == 'extra_kwargs' else {}))
            results[mode] = [v.detach().cpu().numpy().copy() for v in values]
        assert all(a.tobytes() == b.tobytes() for a,b in zip(results['before'], results['after'])), case
        fallback_results[case] = dict(bitwise_equal=True, candidate_count=6, image_batch=batch)
    assert weights_digest() == original_weights, 'Guard changed model state'
    save_json(out / 'guards.json', dict(training_loss_bitwise=True, training_gradients_bitwise=True,
              gradient_FP32=gradient_count, fallback=fallback_results, state_dict_sha256=original_weights,
              topk_methods_AST_unchanged=True))
    print('Training gradients and fallback guards passed', flush=True)

    n = len(dataset)
    stores = {}
    for mode in ('before', 'after'):
        for name, shape in [('boxes', (n,100,5)), ('poses', (n,100,14,3)), ('references', (n,2,100,14,3))]:
            stores[mode,name] = np.lib.format.open_memmap(str(out / (mode + '.' + name + '.npy')),
                                          mode='w+', dtype='<f4', shape=shape)
    stores['input'] = np.lib.format.open_memmap(str(out / 'inputs.npy'), mode='w+',
                                              dtype='<f4', shape=(n,180,60))
    captured, active, branch_batches, decoder_batches = {}, ['before'], {}, {}
    events = {mode:(torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True))
              for mode in ('before','after')}
    hooks = []

    def decoder_pre(module, inputs):
        events[active[0]][0].record()

    def capture(module, inputs, result):
        events[active[0]][1].record()
        states, refs = result
        expected = (2,14,100,256) if active[0] == 'before' else (2,14,1,256)
        assert tuple(states.shape) == expected
        assert tuple(refs.shape) == (2,100,14,3)
        captured[active[0]] = refs.detach().cpu().numpy().copy()

    def layer_pre(module, inputs):
        decoder_batches[active[0]].append(int(inputs[0].shape[1]))

    def branch_pre(module, inputs):
        branch_batches[active[0]].append(int(inputs[0].shape[0]))

    hooks.append(decoder.register_forward_pre_hook(decoder_pre))
    hooks.append(decoder.register_forward_hook(capture))
    for layer in decoder.layers:
        hooks.append(layer.register_forward_pre_hook(layer_pre))
    for branch in head.refine_kpt_branches:
        hooks.append(branch.register_forward_pre_hook(branch_pre))
    metrics, grouped = {'before': [], 'after': []}, {'before': {}, 'after': {}}
    wall_times, decoder_times = {'before': [], 'after': []}, {'before': [], 'after': []}
    compared, max_abs, mismatch_values, all_scores_equal = 0, 0.0, 0, True
    metric_deltas = []
    run_iterator = iter(loader)
    try:
        with (out / 'frames.jsonl').open('x', encoding='utf-8') as ledger:
            for i, data in enumerate(run_iterator):
                assert time.monotonic() - started < budget, 'Evaluation budget exceeded'
                input_tensor = data['img'][0].data[0]
                input_array = input_tensor.detach().cpu().numpy().reshape(180,60).copy()
                assert np.isfinite(input_array).all()
                stores['input'][i] = input_array
                sample = dataset.filename_list[i]
                gt_path = Path(dataset.data_root) / 'keypoint' / (sample + '.npy')
                gt = torch.tensor(np.load(str(gt_path), allow_pickle=False), dtype=torch.float32)
                assert torch.isfinite(gt).all()
                cpu_rng, gpu_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
                order = ('before', 'after') if i % 2 == 0 else ('after', 'before')
                for mode in order:
                    select(mode)
                    active[0] = mode
                    decoder_batches[mode], branch_batches[mode] = [], []
                    torch.set_rng_state(cpu_rng)
                    torch.cuda.set_rng_state_all(gpu_rng)
                    torch.cuda.synchronize()
                    start = time.perf_counter()
                    with torch.no_grad():
                        result = model(return_loss=False, rescale=True, **data)
                    torch.cuda.synchronize()
                    wall_times[mode].append((time.perf_counter()-start)*1000)
                    decoder_times[mode].append(events[mode][0].elapsed_time(events[mode][1]))
                    assert decoder_batches[mode] == ([100,100] if mode == 'before' else [1,1])
                    assert branch_batches[mode] == ([100]*4 if mode == 'before' else [1]*4)
                    assert len(result) == 1
                    boxes_by_class, poses_by_class = result[0]
                    assert len(boxes_by_class) == len(poses_by_class) == 1
                    boxes, poses = boxes_by_class[0], poses_by_class[0]
                    assert boxes.shape == (100,5) and poses.shape == (100,14,3)
                    stores[mode,'boxes'][i] = boxes
                    stores[mode,'poses'][i] = poses
                    stores[mode,'references'][i] = captured[mode]
                # Save complete outputs before inspecting their differences.
                for store in stores.values():
                    store.flush()
                checks = {}
                for name in ('boxes', 'poses', 'references'):
                    a, b = stores['before',name][i], stores['after',name][i]
                    finite = bool(np.isfinite(a).all() and np.isfinite(b).all())
                    delta = float(np.max(np.abs(a.astype(np.float64)-b.astype(np.float64)))) if finite else None
                    unequal = int(np.count_nonzero(a.view('u4') != b.view('u4')))
                    checks[name] = dict(finite=finite, bitwise_equal=unequal == 0,
                                       mismatch_values=unequal, maximum_absolute_difference=delta)
                    compared += a.size
                    mismatch_values += unequal
                    if delta is not None:
                        max_abs = max(max_abs, delta)
                score_equal = stores['before','boxes'][i,:,4].tobytes() == stores['after','boxes'][i,:,4].tobytes()
                all_scores_equal = all_scores_equal and score_equal
                assert input_array.tobytes() == input_tensor.detach().cpu().numpy().reshape(180,60).tobytes()
                within_bound = all(c['finite'] and c['maximum_absolute_difference'] <= atol for c in checks.values())
                if not score_equal or not within_bound:
                    save_json(out / 'first-discrepancy.json', dict(index=i, sample=sample,
                              checks=checks, scores_bitwise=score_equal))
                    raise RuntimeError('Saved output exceeds comparison bound; stop without retry')
                frame_metrics = {}
                for mode in ('before','after'):
                    pred = torch.tensor(stores[mode,'poses'][i].copy(), dtype=torch.float32)
                    row = [float(v) for v in dataset.calc_mpjpe(gt, pred, sample, root=[5,7])]
                    assert np.isfinite(row).all()
                    metrics[mode].append(row)
                    grouped[mode].setdefault(str(len(gt)), []).append(row[0])
                    frame_metrics[mode] = row
                metric_deltas.append(frame_metrics['after'][0] - frame_metrics['before'][0])
                ledger.write(json.dumps(dict(index=i, sample=sample, persons=len(gt),
                       gt_sha256=sha(gt_path), input_sha256=hashlib.sha256(input_array.tobytes()).hexdigest(),
                       checks=checks, scores_bitwise=score_equal, metric_mm=frame_metrics,
                       model_wall_ms={m:wall_times[m][-1] for m in wall_times},
                       decoder_cuda_ms={m:decoder_times[m][-1] for m in decoder_times}), allow_nan=False) + '\n')
                ledger.flush()
                if (i+1) % 100 == 0 or i == 0:
                    progress = dict(status='running', completed=i+1, total=n,
                                    seconds=time.monotonic()-started, max_abs=max_abs,
                                    mismatch_values=mismatch_values)
                    save_json(out / 'progress.json', progress)
                    print(json.dumps(progress), flush=True)
        assert len(metrics['before']) == len(metrics['after']) == n
        for name, expected in pins.items():
            assert sha(ROOT / name) == expected
        assert source_path.read_bytes() == (out / 'transformer.after.py').read_bytes()
        assert head_path.read_bytes() == (out / 'petr_head.after.py').read_bytes()
        assert weights_digest() == original_weights
        metric_names = ['mpjpe','mpjpeh','mpjpev','mpjped']

        def timing_summary(rows):
            values = np.asarray(rows[10:])
            return dict(first_ms=rows[0], excluded_first_frames=10, measured_frames=len(values),
                        mean_ms=float(values.mean()), median_ms=float(np.median(values)),
                        p95_ms=float(np.percentile(values,95)))

        final = dict(status='full7824_paired_inference_completed', frames=n,
                     compared_FP32=compared, maximum_absolute_difference=max_abs,
                     mismatch_values=mismatch_values, all_outputs_bitwise=mismatch_values == 0,
                     all_scores_bitwise=all_scores_equal, topk_retained=2, candidates=100,
                     metric_protocol=preflight['metric'],
                     metrics={mode:dict(zip(metric_names,np.mean(metrics[mode],axis=0).tolist())) for mode in metrics},
                     by_person_count={mode:{k:dict(frames=len(v),mpjpe=float(np.mean(v)))
                                             for k,v in grouped[mode].items()} for mode in grouped},
                     frame_mpjpe_delta_mm=dict(maximum=float(max(metric_deltas)), minimum=float(min(metric_deltas)),
                                              maximum_absolute=float(np.abs(metric_deltas).max())),
                     timing=dict(model_wall={m:timing_summary(v) for m,v in wall_times.items()},
                                 refine_decoder_cuda={m:timing_summary(v) for m,v in decoder_times.items()},
                                 caveat=preflight['timing']),
                     seconds=time.monotonic()-started, weights_changed=False, retrained=False,
                     board_deployment_changed=False, source_before_sha256=preflight['source_sha256'],
                     source_after_sha256=preflight['after_sha256'])
        final['mpjpe_delta_mm'] = final['metrics']['after']['mpjpe']-final['metrics']['before']['mpjpe']
        final['numerical_gate_passed'] = abs(final['mpjpe_delta_mm']) <= metric_limit_mm
        final['output_sha256'] = {p.name:sha(p) for p in sorted(out.glob('*.npy'))}
        save_json(out / 'summary.json', final)
        assert final['numerical_gate_passed'], 'Mean MPJPE bound exceeded; complete outputs saved'
        save_json(out / 'progress.json', dict(status='complete', completed=n, total=n))
        print(json.dumps(final), flush=True)
    finally:
        for hook in hooks:
            hook.remove()
        select('after')
        for store in stores.values():
            store.flush()
        if hasattr(run_iterator, '_shutdown_workers'):
            run_iterator._shutdown_workers()


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if '--output' in sys.argv:
            folder = Path(sys.argv[sys.argv.index('--output')+1])
            if folder.is_dir():
                save_json(folder / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc()))
        raise
