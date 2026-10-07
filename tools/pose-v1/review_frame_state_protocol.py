"""Independently verify existing frame-state traces, without accessing a device."""
import argparse
import json
from pathlib import Path
import numpy as np
from mixed_validation_gate import verify, load, lines, save, fusion_binding_review
from host_content_review import review_mixed

def review(results, package):
    verified=verify(results); verify(package)
    out=results/'results'; config=load(out/'run-config.json')
    assert type(config['frame_state_reset_level']) is int and config['frame_state_reset_level']==1
    assert config['device_init_allowed'] is True and config['cases'] in ('one','three')
    assert (results/'exit.txt').read_text().strip()=='0' and not (out/'failure.json').exists()
    baseline=load(package/'mixed-fusion-baseline.json')
    fusion_binding_review(out,baseline)
    calls=[('S11_01_308',6)] if config['cases']=='one' else [
        ('S11_01_308',6),('S11_01_309',7),('S11_01_310',8),('S11_01_308',6)]
    captures=review_mixed(out,package/'reference',calls)
    state=lines(out/'readiness.jsonl'); summaries=[]
    assert all(type(r['layer_count']) is int and type(r['invocation']) is int and
        isinstance(r['ready'],list) and all(type(v) is bool for v in r['ready']) for r in state)
    for inv,(name,frame) in enumerate(calls):
        rows=[r for r in state if r['invocation']==inv]
        assert len(rows)==19 and all(r['frame_id']==frame for r in rows)
        def event(where):
            found=[r for r in rows if r['where']==where]
            assert len(found)==1
            return found[0]
        before_clear=event('before_frame_state_clear'); start=event('before_forward')
        assert before_clear['layer_count']==(0 if inv==0 else 745)
        assert start['layer_count']==0 and start['ready']==[True]
        for where in ('after_forward','outputs_completed','after_dump'):
            r=event(where)
            assert r['layer_count']==745 and r['ready']==[True,True]
        groups=[r for r in rows if r['where']=='post_callback' and 9185<=r['op_id']<=9191]
        assert len(groups)==7 and len({r['op_id'] for r in groups})==7
        for r in groups:
            # Fixed baseline checked independently above; per-group end counts.
            minimum={9185:223,9186:234,9187:477,9188:481,9189:638,9190:720,9191:745}[r['op_id']]
            assert minimum<=r['layer_count']<=745 and all(r['ready'])
        summaries.append(dict(invocation=inv,case=name,start_count=start['layer_count'],
            before_clear_count=before_clear['layer_count'],end_count=event('outputs_completed')['layer_count']))
    outputs=[]
    for name in ('S11_01_308',) if len(calls)==1 else ('S11_01_308','S11_01_309','S11_01_310'):
        data={}
        for kind,count in [('scores',100),('poses',4200)]:
            p=out/f'{name}.{kind}.f32';raw=p.read_bytes(); a=np.frombuffer(raw,dtype='<f4')
            assert a.size==count and np.isfinite(a).all()
            import hashlib
            data[kind]=hashlib.sha256(raw).hexdigest()
        outputs.append(dict(case=name,**data))
    if len(calls)==4:
        assert len({r['scores'] for r in outputs})==3 and len({r['poses'] for r in outputs})==3
        for kind in ('scores','poses'):
            assert (out/f'S11_01_308.repeat.{kind}.f32').read_bytes()==(out/f'S11_01_308.{kind}.f32').read_bytes()
        # Stronger evidence: every captured Host bridge value repeats with first input.
        raw={(r['invocation'],r['kind'],r['op_id'],r['slot']):(out/'content'/r['file']).read_bytes() for r in captures}
        for key,value in raw.items():
            if key[0]==3: assert value==raw[(0,)+key[1:]]
    return dict(status='frame_state_protocol_verified',returned_files_verified=verified,
        calls=summaries,outputs=outputs,content_records=len(captures),same_session_repeat_all_captured_content_equal=len(calls)==4,
        numerical_accepted=False,performance_accepted=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('results','package','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); save(a.output,review(a.results,a.package))
    print('Frame-state protocol and content checked; numeric/performance tolerance remains separate.')
