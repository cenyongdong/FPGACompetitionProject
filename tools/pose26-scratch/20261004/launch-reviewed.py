import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/public/cyd/Person-in-WiFi-3D-repo')
OUT=ROOT/'result/tpami2026_scratch_20261004'
assert not (OUT/'pipeline-launched.lock').exists()
assert not (OUT/'pipeline-launch.json').exists()
for name in ('unit_gate','ddp_gate'):
 assert json.loads((OUT/'gates'/f'{name}.json').read_text())['passed']
env=os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='1,2,3,4',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',PYTHONPATH=str(ROOT))
cmd=[sys.executable,'-B','tools/pose26_scratch/run_experiment.py']
with (OUT/'pipeline.stdout.log').open('x') as log:
 child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record={'pid':child.pid,'command':cmd,'cwd':str(ROOT),'time':datetime.datetime.now().isoformat(),'fresh_initialization':True,'optimizer':'Adam','max_epochs':500,'automatic_retry':False,'automatic_extension':False,'gpu_ids':[1,2,3,4]}
(OUT/'pipeline-launch.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
