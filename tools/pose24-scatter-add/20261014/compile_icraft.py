"""Bounded five-stage host Icraft conversion with the actual retained TOML.
No board/SSH/inference operation. Every stage checks exit code, JSON/RAW and MD5.
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import subprocess
import time
import traceback

ROOT=Path(r'D:/FPGACompetitionProject')
OUT=ROOT/'model/piw24_noscatter-20261014-r3'
CONFIG=OUT/'piw24_noscatter.toml'
RUNTIME=ROOT/'.local/icraft-runtime/cuda-11.8.0/runtime-manifest.json'
BIN=Path(r'C:/Icraft/CLI v3.39.0/bin')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def graph_review(stage):
    suffix={'parse':'parsed','optimize':'optimized','quantize':'quantized',
            'adapt':'adapted','generate':'ZG'}[stage]
    jp=OUT/f'piw24_noscatter_{suffix}.json'
    rp=OUT/f'piw24_noscatter_{suffix}.raw'
    assert jp.is_file() and rp.is_file(), 'Expected stage pair missing'
    graph=json.loads(jp.read_text(encoding='utf-8'))
    assert graph['ai_target']=='@zhuget(330)'
    assert graph['icraft_version']=='v3.39.0'
    assert graph['params_bytes']==rp.stat().st_size
    md5=hashlib.md5(rp.read_bytes()).hexdigest()
    assert md5==graph['params_md5'], 'Graph/RAW MD5 mismatch'
    counts=collections.Counter(op['_type_key'] for op in graph['ops'])
    assert counts.get('icraft::xir::ScatterND',0)==0
    inputs=[op for op in graph['ops'] if op['_type_key']=='icraft::xir::Input']
    outputs=[op for op in graph['ops'] if op['_type_key']=='icraft::xir::Output']
    assert len(inputs)==len(outputs)==1
    assert inputs[0]['outputs'][0]['dtype']['shape']==[1,180,60]
    assert [x['dtype']['shape'] for x in outputs[0]['inputs']]==[[1,100],[1,100,14,3]]
    assert inputs[0]['outputs'][0]['dtype']['element_dtype']=='@fp(32)'
    assert all(v['dtype']['element_dtype']=='@fp(32)' for v in outputs[0]['inputs'])
    host=[dict(id=op['op_id'],type=op['_type_key']) for op in graph['ops']
          if op['compile_target']=='@hostt' and op['_type_key'] not in ('icraft::xir::Input','icraft::xir::Output')]
    precision=collections.Counter()
    for op in graph['ops']:
        if op['_type_key']=='icraft::xir::Matmul':
            value=op['inputs'][0]['dtype']['element_dtype']
            precision[value['storage_dtype'] if isinstance(value,dict) else value]+=1
    result=dict(stage=stage,json=jp.name,raw=rp.name,json_bytes=jp.stat().st_size,
                raw_bytes=rp.stat().st_size,json_sha256=sha(jp),raw_sha256=sha(rp),
                raw_md5_verified=md5,operators=dict(counts),host_compute=host,
                Matmul_input_storage=dict(precision),logical_ops=len(graph['ops']),
                fixed_FP32_ports_verified=True,ScatterND=0,target='ZG330',
                hardop_layer_count_sum=sum(op.get('layer_count',0) for op in graph['ops']))
    save(OUT/'logs'/f'{stage}.graph-review.json',result)
    return result


def main():
    assert not (OUT/'preflight.json').exists(), 'Fresh conversion run required'
    config_sha=sha(CONFIG)
    assert sha(OUT/'source/person_in_wifi_2024_best_epoch442_full_noscatter.onnx')=='a8c3261b614cc14e6b4818d0efaf8a61dc3127bbe08020096600e654bc1b9c75'
    runtime=json.loads(RUNTIME.read_text(encoding='utf-8'))
    assert runtime['icraft_version']=='3.39.0'
    search=[str(BIN)]
    dlls={}
    for component in runtime['components']:
        search+=component['bin_dirs']
        for item in component['dlls']:
            path=Path(item['path'])
            assert sha(path)==item['sha256']
            dlls[str(path)]=item['sha256']
    assert len(dlls)==3
    env=dict(os.environ)
    env['PATH']=';'.join(search)+';'+env.get('PATH','')
    env['PYTHONDONTWRITEBYTECODE']='1'
    exe=BIN/'icraft.exe'
    executables={p.name:sha(p) for p in BIN.glob('icraft*.exe')}
    preflight=dict(working_directory=str(OUT),actual_config=str(CONFIG),config_sha256=config_sha,
                   source_ONNX_SHA256=sha(OUT/'source/person_in_wifi_2024_best_epoch442_full_noscatter.onnx'),
                   runtime_manifest_sha256=sha(RUNTIME),DLL_verified=dlls,
                   executables=executables,budget_seconds=3600,stage_timeout_seconds=1200,
                   target='ZG330',qdtype='fp16',preprocess='nop, FP32 CSI [1,180,60]',
                   original_TOML_missing=True,precision_basis='old 130 Matmul inputs/weights FP16; SDK TF32 intermediary casts allowed',
                   board_or_runtime_inference=False,automatic_retry=False,
                   stop='nonzero exit/timeout/missing pair/identity drift/RAW MD5 mismatch/ScatterND/port mismatch')
    save(OUT/'preflight.json',preflight)
    begin=time.monotonic()
    records=[]
    for stage in ('parse','optimize','quantize','adapt','generate'):
        assert sha(CONFIG)==config_sha
        assert time.monotonic()-begin<3600
        arguments=[str(exe),stage,CONFIG.name]
        # Validate the retained TOML through the CLI's real command expansion.
        dry=subprocess.run(arguments+['--dry_run'],cwd=OUT,env=env,capture_output=True,timeout=60)
        (OUT/'logs'/f'{stage}.dry-run.stdout.log').write_bytes(dry.stdout)
        (OUT/'logs'/f'{stage}.dry-run.stderr.log').write_bytes(dry.stderr)
        assert dry.returncode==0, 'TOML expansion failed'
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        step=time.monotonic()
        log=OUT/'logs'
        with (log/f'{stage}.stdout.log').open('xb') as stdout, (log/f'{stage}.stderr.log').open('xb') as stderr:
            process=subprocess.Popen(arguments,cwd=OUT,env=env,stdout=stdout,stderr=stderr)
            save(log/f'{stage}.invocation.json',dict(command=arguments,cwd=str(OUT),pid=process.pid,
                                                     started_UTC=started,config_sha256=config_sha))
            try:
                code=process.wait(timeout=min(1200,max(1,3600-(time.monotonic()-begin))))
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                process.wait()
                save(log/f'{stage}.timeout.json',dict(pid=process.pid,elapsed=time.monotonic()-step))
                raise
        result=dict(stage=stage,exit_code=code,seconds=time.monotonic()-step)
        save(log/f'{stage}.exit.json',result)
        assert code==0, f'{stage} failed with exit {code}; stop'
        result['graph']=graph_review(stage)
        records.append(result)
        save(OUT/'progress.json',dict(status='running',completed_stages=[r['stage'] for r in records]))
        print(json.dumps(dict(stage=stage,exit=code,seconds=result['seconds'],
                             ops=result['graph']['logical_ops'],raw_bytes=result['graph']['raw_bytes'])),flush=True)
    assert sha(CONFIG)==config_sha
    summary=dict(status='five_stage_host_conversion_passed',stages=records,
                 config_sha256=config_sha,seconds=time.monotonic()-begin,
                 board_tested=False,numerical_inference_tested=False,
                 current_deployed_baseline_replaced=False)
    save(OUT/'summary.json',summary)
    inventory={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*'))
               if p.is_file() and p.name not in ('pipeline.stdout.log','pipeline.stderr.log')}
    save(OUT/'files.json',inventory)
    print(json.dumps(dict(status=summary['status'],seconds=summary['seconds'],config_sha256=config_sha)),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        save(OUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),retry=False))
        raise
