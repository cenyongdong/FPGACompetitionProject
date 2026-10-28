"""CPU construction/strict-loading check only: no dataset, forward, optimizer, GPU."""
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--algorithm-root',required=True,type=Path)
    p.add_argument('--work',required=True,type=Path);p.add_argument('--checkpoint',required=True,type=Path)
    a=p.parse_args();work=a.work.resolve();algo=a.algorithm_root.resolve()
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Run with CUDA_VISIBLE_DEVICES empty for this CPU-only check')
    import torch
    torch.set_num_threads(2)
    if not (work/'planned-run/config.py').is_file():
        subprocess.run([sys.executable,str(Path(__file__).with_name('prepare_finetune.py')),
            '--algorithm-root',str(algo),'--dataset',str(work/'paired-data'),'--checkpoint',str(a.checkpoint),
            '--output',str(work/'planned-run'),'--allow-pending-data'],check=True)
    sys.path.insert(0,str(algo));sys.path.insert(0,str(Path(__file__).resolve().parent))
    from mmcv import Config
    cfg=Config.fromfile(str(work/'planned-run/config.py'))
    for module in cfg.custom_imports['imports']:importlib.import_module(module)
    from opera.models.builder import build_model
    model=build_model(cfg.model);model.init_weights()
    state=torch.load(a.checkpoint,map_location='cpu')['state_dict']
    state={k[7:] if k.startswith('module.') else k:v for k,v in state.items()}
    if set(model.state_dict())!=set(state) or not all(torch.equal(value,model.state_dict()[name]) for name,value in state.items()):
        raise ValueError('A starting parameter differs from original epoch99')
    report=dict(model_constructed_on_CPU=True,exact_checkpoint_loaded=True,checkpoint_tensors=len(state),
        initialization=model.migration_report,config_loader_passed=True,GPU_used=False,forward_calls=0,
        optimizer_created=False,training_steps=0,data_ready=False,
        note='Training adapter load validated; actual paired data and training remain unvalidated/unstarted.')
    (work/'training-readiness.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
