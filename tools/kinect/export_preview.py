"""Freeze the current best local-data checkpoint; export and verify on CPU."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ['CUDA_VISIBLE_DEVICES'] = ''


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run, out = args.run.resolve(), args.output.resolve()
    plan = json.loads((run/'preparation.json').read_text())
    rows = [json.loads(line) for line in (run/'validation.jsonl').read_text().splitlines()]
    best = min(range(len(rows)), key=lambda i: rows[i]['metrics']['top1_mpjpe'])
    source = run/('best_top1_mpjpe_epoch_'+str(best+1)+'.pth')
    status_path = run.parent/(run.name+'-status.json')
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    final_checkpoint = (status.get('stage') == 'completed'
                        and status.get('best_checkpoint') == str(source)
                        and status.get('best_epoch') == best+1)
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out/'checkpoint.pth'
    digest = hashlib.sha256()
    # Opening the selected file once protects this snapshot from later best-file
    # replacement/deletion by the still-running training job.
    with source.open('rb') as src, snapshot.open('xb') as dst:
        while True:
            chunk = src.read(4*1024*1024)
            if not chunk:
                break
            dst.write(chunk)
            digest.update(chunk)
    identity = dict(source_checkpoint=str(source), best_epoch=best+1,
                    selection=rows[best], snapshot_sha256=digest.hexdigest(),
                    bytes=snapshot.stat().st_size, frozen_at=time.time(),
                    final_training_checkpoint=final_checkpoint,
                    initialization=status.get('initialization'), device='cpu', threads=2)
    save(out/'checkpoint-identity.json', identity)
    sys.path.insert(0, str(run.parent/'tools'))
    sys.path.insert(0, str(Path(plan['algorithm_root'])/'tools/pose180'))
    from common import setup, torch, np
    from export import FullGraph
    import onnx
    import onnxruntime as ort

    start = time.monotonic()
    cfg, model = setup('cpu', config=str(run/'config.py'))
    state = torch.load(snapshot, map_location='cpu')['state_dict']
    state = {k[7:] if k.startswith('module.') else k: v for k, v in state.items()}
    model.load_state_dict(state, strict=True)
    wrapped = FullGraph(model).eval()
    data = Path(plan['dataset'])/'train_data'
    tokens = np.load(data/'tokens.npy', mmap_mode='r')
    names = json.loads((data/'names.json').read_text())
    indices = [0, len(tokens)//2, len(tokens)-1]
    xs = torch.from_numpy(np.array(tokens[indices], copy=True))
    onnx_dir, fixtures = out/'onnx', out/'fixtures'
    onnx_dir.mkdir(); fixtures.mkdir()
    path = onnx_dir/'pose180_shared.onnx'
    with torch.no_grad():
        torch.onnx.export(wrapped, (xs[:1],), str(path), opset_version=11,
                          input_names=['csi_tokens'], output_names=['scores', 'poses'],
                          do_constant_folding=True)
    graph = onnx.load(str(path)); onnx.checker.check_model(graph)
    operators = dict(Counter(node.op_type for node in graph.graph.node))
    if any(operators.get(k, 0) for k in ('TopK', 'ScatterND', 'GatherElements')):
        raise ValueError('Unexpected candidate selection operations')
    shapes = [[d.dim_value for d in value.type.tensor_type.shape.dim]
              for value in list(graph.graph.input)+list(graph.graph.output)]
    if shapes != [[1,180,60], [1,180], [1,180,14,3]]:
        raise ValueError('Unexpected public ports: '+str(shapes))
    options = ort.SessionOptions(); options.intra_op_num_threads=2; options.inter_op_num_threads=1
    session = ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])
    comparisons, cases = [], []
    for i, index in enumerate(indices):
        name = 'local_train_'+str(index)
        x = xs[i:i+1]
        with torch.no_grad():
            expected = [value.numpy().copy() for value in wrapped(x)]
        actual = session.run(None, {'csi_tokens': x.numpy()})
        x.numpy().astype('<f4').tofile(fixtures/(name+'.input.f32'))
        differences = {}
        for label, reference, value in zip(('scores','poses'), expected, actual):
            reference.astype('<f4').tofile(fixtures/(name+'.fp32.'+label+'.f32'))
            np.save(onnx_dir/(name+'.'+label+'.pytorch.npy'), reference)
            np.save(onnx_dir/(name+'.'+label+'.ort.npy'), value)
            differences[label] = float(np.max(np.abs(reference.astype('f8')-value.astype('f8'))))
        comparisons.append(dict(sample=names[index], row=index, max_abs=differences,
                                finite=all(np.isfinite(v).all() for v in actual)))
        cases.append(dict(name=name, source_sample=names[index], split='train', row=index,
                          input_shape=[1,180,60], score_shape=[1,180], pose_shape=[1,180,14,3], gt_people=1))
    passed = all(row['finite'] and max(row['max_abs'].values()) <= 2e-5 for row in comparisons)
    save(fixtures/'cases.json', cases)
    save(onnx_dir/'verification.json', dict(passed=passed, checkpoint=identity,
         loaded_tensors=len(state), operators=operators, port_shapes=shapes,
         comparisons=comparisons, seconds=time.monotonic()-start,
         onnx_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), device='cpu', threads=2))
    if not passed:
        raise ValueError('ONNX numerical verification failed; actual outputs preserved')
    save(out/'complete.json', dict(passed=True, best_epoch=best+1, onnx=str(path), seconds=time.monotonic()-start))
    print(json.dumps(dict(passed=True,best_epoch=best+1,comparisons=comparisons,seconds=time.monotonic()-start)), flush=True)


if __name__ == '__main__':
    main()
