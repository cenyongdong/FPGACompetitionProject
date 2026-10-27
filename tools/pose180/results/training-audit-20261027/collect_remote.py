"""Read-only CPU audit; stream to the server's existing Python environment."""
import gc
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
from datetime import datetime, timezone, timedelta

import torch
from mmcv import Config

torch.set_num_threads(2)
root = Path('/public/cyd/Person-in-WiFi-3D-repo')


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def compact(cfg):
    output = {key: cfg.get(key) for key in ['optimizer', 'optimizer_config',
        'lr_config', 'runner', 'seed', 'gpu_ids', 'resume_from', 'load_from', 'custom_hooks']}
    output['data'] = {key: cfg.data.get(key) for key in
                      ['samples_per_gpu', 'workers_per_gpu', 'train', 'val', 'test']}
    model = cfg.model
    output['model'] = dict(type=model.type, source_checkpoint=model.get('source_checkpoint'),
        query=model.bbox_head.num_query,
        decoder_layers=model.bbox_head.transformer.decoder.num_layers,
        refine_layers=model.bbox_head.transformer.refine_decoder.num_layers,
        loss_cls=model.bbox_head.loss_cls, loss_kpt=model.bbox_head.loss_kpt,
        loss_kpt_refine=model.bbox_head.loss_kpt_refine, train_cfg=model.get('train_cfg'),
        backbone_init=model.backbone.get('init_cfg'))
    return output


output = dict(checked_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),
              checkpoints={}, runs={}, source_files={}, data_lists={})
checkpoints = {
    'original442': 'result/code_faithful/best_mpjpe_epoch_442.pth',
    'scratch_best130': 'result/piw24_pose180_scratch_20261024_extra100_r2/best_mpjpe_epoch_130.pth',
    'branch230': 'result/piw24_pose180_scratch_best130_next100_20261026_r1/epoch_230.pth'}
for label, name in checkpoints.items():
    checkpoint = torch.load(root / name, map_location='cpu')
    meta, optimizer = checkpoint.get('meta', {}), checkpoint.get('optimizer', {})
    steps = [float(state['step']) for state in optimizer.get('state', {}).values() if 'step' in state]
    groups = optimizer.get('param_groups', [])
    cfg = Config.fromstring(meta['config'], '.py') if meta.get('config') else None
    query = checkpoint['state_dict']['bbox_head.query_embedding.weight']
    output['checkpoints'][label] = dict(path=name, epoch=meta.get('epoch'),
        iteration=meta.get('iter'), meta_keys=list(meta), top_level_keys=list(checkpoint),
        hook_msgs=meta.get('hook_msgs'), optimizer_entries=len(optimizer.get('state', {})),
        optimizer_step_range=[min(steps), max(steps)] if steps else None,
        lr_values=sorted(set(group['lr'] for group in groups)),
        initial_lr_values=sorted(set(group.get('initial_lr', group['lr']) for group in groups)),
        betas=sorted(set(str(group.get('betas')) for group in groups)),
        eps=sorted(set(group.get('eps') for group in groups)),
        weight_decay=sorted(set(group.get('weight_decay') for group in groups)),
        query_shape=list(query.shape),
        query_sha256=hashlib.sha256(query.numpy().tobytes()).hexdigest(),
        config=compact(cfg) if cfg else None)
    del checkpoint, optimizer, query, groups
    gc.collect()

for label, directory in {
        'scratch100': 'piw24_pose180_scratch_20261023_r1',
        'scratch200': 'piw24_pose180_scratch_20261024_extra100_r2',
        'branch230': 'piw24_pose180_scratch_best130_next100_20261026_r1'}.items():
    folder = root / 'result' / directory
    epochs = {}
    with (folder / 'progress.jsonl').open() as stream:
        for line in stream:
            record = json.loads(line)
            epoch = epochs.setdefault(str(record['epoch']), dict(records=0, losses=[], rates=set()))
            epoch['records'] += 1
            epoch['rates'].add(tuple(record.get('lr', [])))
            if record['stage'] == 'training':
                loss = (record.get('metrics') or {}).get('loss')
                if loss is not None:
                    epoch['losses'].append(loss)
    for epoch in epochs.values():
        values = epoch.pop('losses')
        epoch['loss'] = dict(mean=statistics.mean(values), last20_mean=statistics.mean(values[-20:]),
                            min=min(values), max=max(values)) if values else None
        epoch['rates'] = list(epoch['rates'])
    evaluations = [json.loads(line) for line in (folder / 'evaluations.jsonl').read_text().splitlines() if line.strip()]
    log = folder / 'training.stderr.log'
    if not log.is_file():
        log = folder / 'jobs/formal-r1/stderr.log'
    norms = []
    if log.is_file():
        for line in log.open(errors='replace'):
            match = re.search(r'Epoch \[(\d+)\].*?grad_norm:\s*([\d.eE+-]+)', line)
            if match:
                norms.append(float(match.group(2)))
    output['runs'][label] = dict(epochs=epochs, evaluations=evaluations,
        resumption=read(folder / 'resumption.json'), manifest=read(folder / 'resume_manifest.json'),
        clip_diagnostics=dict(logged_steps=len(norms), median_norm=statistics.median(norms) if norms else None,
            fraction_above_0_1=sum(norm > .1 for norm in norms) / len(norms) if norms else None,
            median_clip_scale=statistics.median([.1 / norm for norm in norms if norm > .1]) if norms else None))

for name in ['opera/datasets/wifi_pose.py', 'opera/models/pose180/head.py',
        'opera/models/pose180/transformer.py', 'opera/models/pose180/hooks.py',
        'opera/models/pose180/resume.py', 'opera/models/dense_heads/petr_head.py',
        'opera/core/bbox/assigners/hungarian_assigner.py', 'opera/models/utils/transformer.py']:
    path = root / name
    if path.is_file():
        output['source_files'][name] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest())

names_by_split = {}
for split in ['train', 'test']:
    path = root / 'data/wifipose' / (split + '_data') / (split + '_data_list.txt')
    lines = path.read_text().splitlines()
    names = [line.split()[0] for line in lines if line.strip()]
    names_by_split[split] = names
    output['data_lists'][split] = dict(path=str(path),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), nonempty=len(names), unique=len(set(names)),
        first_blank_line=next((index + 1 for index, line in enumerate(lines) if not line.strip()), None),
        prefix_people_counts={str(i): sum(name.startswith('S1' + str(i) + '_') for name in names) for i in [1, 2, 3]},
        first3=names[:3], last3=names[-3:])
output['overlap_train_test'] = len(set(names_by_split['train']) & set(names_by_split['test']))
print(json.dumps(output, ensure_ascii=False,
                 default=lambda obj: list(obj) if isinstance(obj, (range, set)) else str(obj)))
