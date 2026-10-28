"""Inspect a prepared configuration; train only with an explicit --execute."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare_finetune import dataset_status


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--gpus',help='Explicit physical GPU indices, for example 1,6')
    p.add_argument('--execute',action='store_true')
    a=p.parse_args();bundle=a.bundle.resolve();plan=json.loads((bundle/'preparation.json').read_text(encoding='utf-8-sig'))
    dataset=Path(plan['dataset']);manifest_path=dataset/'dataset.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig')) if manifest_path.is_file() else {}
    profile=dataset_status(manifest,bool(plan.get('experimental_receipt_supervision')));ready=profile['ready']
    status=dict(training_started=False,dataset_ready=ready,bundle=str(bundle),
        experimental_receipt_supervision=profile['experimental'],certified_supervision=profile['certified'],
        physical_time_alignment_verified=profile['certified'],
        original_checkpoint=plan['starting_checkpoint'],requires_explicit_execute=True,
        mmcv_available=importlib.util.find_spec('mmcv') is not None,
        note='Prepare and run this bundle on the existing Linux training environment; no driver/SDK/FPGA changes needed.')
    print(json.dumps(status,indent=2))
    if not a.execute:return
    if not ready or not status['mmcv_available']:raise ValueError('Real paired data and the existing training environment are required')
    if not plan['data_ready']:raise ValueError('Regenerate the configuration against the completed dataset before training')
    if not a.gpus:raise ValueError('Specify available physical GPUs explicitly; no automatic GPU assignment')
    ids=a.gpus.split(',')
    if not all(i.isdigit() for i in ids) or len(set(ids))!=len(ids):raise ValueError('Invalid GPU indices')
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True)
    by_index={row.split(',')[0].strip():row.split(',')[1].strip() for row in inventory.splitlines()}
    if not set(ids).issubset(by_index):raise ValueError('Selected GPU is absent')
    active=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
    if any(row.split(',')[0].strip() in {by_index[i] for i in ids} for row in active.splitlines()):
        raise ValueError('A selected GPU is occupied; existing jobs are left untouched')
    if (bundle/'initialization.json').exists():raise ValueError('This training bundle has already run; create an independent new run')
    env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=a.gpus;env['OMP_NUM_THREADS']='2'
    command=[sys.executable,'-m','torch.distributed.run','--standalone','--nproc_per_node='+str(len(ids)),
        str(Path(plan['algorithm_root'])/'tools/pose180/train.py'),str(bundle/'config.py'),'--launcher','pytorch','--seed','0']
    with (bundle/'launch.json').open('x') as file:json.dump(dict(command=command,physical_gpus=ids),file,indent=2)
    raise SystemExit(subprocess.call(command,cwd=plan['algorithm_root'],env=env))


if __name__=='__main__':main()
