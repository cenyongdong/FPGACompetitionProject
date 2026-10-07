"""Synthetic offline tests of r4 content validation. No C++/SDK/model execution."""
import argparse
import copy
import json
from pathlib import Path
import runpy
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    assert not a.output.exists(), 'Preserve earlier tests'
    api = runpy.run_path(str(Path(__file__).with_name('host_content_review.py')))
    a.output.mkdir(parents=True)
    tests = []
    def emit(folder, rows, raw):
        (folder / 'content').mkdir(parents=True)
        (folder / 'content/index.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')
        for r in rows:
            (folder / 'content' / r['file']).write_bytes(raw[r['file']])
    def row(inv, case, frame, kind, op, slot, value, **extra):
        name = f'call{inv}.{kind}.op{op}.slot{slot}.f32'
        return dict(invocation=inv, case=case, frame_id=frame, kind=kind, op_id=op, slot=slot,
                    file=name, bytes=len(value), tensor=dict(allocated=True, bytes=len(value), pointer='CPTR',
                    region='icraft::xrt::HostMemRegionNode', offset=0, chunk_bytes=len(value)), **extra)
    host_rows, host_raw = [], {}
    for inv in (0, 1):
        v=(np.arange(10800, dtype=np.float32)%np.float32(127))/np.float32(16)-np.float32(4)+np.float32(inv/8)
        v[0]=np.float32(-0.) if inv==0 else np.float32(0.)
        for kind in ('caller_input', 'input0_output'):
            value=v.astype('<f4').tobytes()
            r=row(inv, f'HOST_SMOKE_{inv}',100+inv,kind,0,0,value,matches_expected=True,
                  same_handle_as_caller=True,same_chunk_as_caller=True)
            host_rows.append(r);host_raw[r['file']]=value
    value=host_raw[host_rows[-1]['file']]
    r=row(2,'HOST_NEGATIVE',102,'expected_mismatch',0,0,value,matches_expected=False,
          same_handle_as_caller=True,same_chunk_as_caller=True)
    host_rows.append(r);host_raw[r['file']]=value
    host=a.output/'synthetic-host';emit(host,host_rows,host_raw)
    (host/'host-content-check.json').write_text(json.dumps(dict(status='host_content_paths_passed',rounds=2,
        positive_records=4,expected_mismatch_rejected=True,unallocated_rejected=True,FP16_rejected=True,
        device_opened=False,session_created=False)),encoding='utf-8')
    api['review_host'](host)
    calls=[('S11_01_308',6),('S11_01_309',7),('S11_01_310',8),('S11_01_308',6)]
    records,raw=[],{}
    for inv,(case,frame) in enumerate(calls):
        value=(a.reference/(case+'.input.f32')).read_bytes()
        for kind in ('caller_input','input0_output'):
            r=row(inv,case,frame,kind,0,0,value,matches_expected=True,
                  same_handle_as_caller=True,same_chunk_as_caller=True)
            records.append(r);raw[r['file']]=value
        for kind,sizes in [('bridge_input',api['INPUT_SIZES']),('bridge_result',api['RESULT_SIZES'])]:
            for (op,slot),size in sizes.items():
                value=(np.arange(size//4,dtype=np.float32)+np.float32((0 if inv==3 else inv)/4)).astype('<f4').tobytes()
                r=row(inv,case,frame,kind,op,slot,value);records.append(r);raw[r['file']]=value
    full=a.output/'synthetic-four-calls';emit(full,records,raw)
    api['review_mixed'](full,a.reference,calls)
    one=a.output/'synthetic-one-call';single=[r for r in records if r['invocation']==0];emit(one,single,raw)
    api['review_mixed'](one,a.reference,calls[:1])
    def rejected(name,mutate):
        changed,data=copy.deepcopy(records),copy.deepcopy(raw)
        mutate(changed,data)
        target=a.output/name;emit(target,changed,data)
        try:api['review_mixed'](target,a.reference,calls)
        except (ValueError,KeyError) as error:tests.append(dict(case=name,rejected=True,reason=str(error)))
        else:raise AssertionError('Invalid capture accepted: '+name)
    rejected('missing_bridge_record',lambda r,d:r.pop())
    rejected('metadata_ADDR',lambda r,d:r[0]['tensor'].update(pointer='ADDR'))
    rejected('unsafe_bounds',lambda r,d:r[0]['tensor'].update(offset=1))
    rejected('numeric_boolean',lambda r,d:r[0].update(matches_expected=1))
    rejected('boolean_invocation',lambda r,d:r[0].update(invocation=True))
    rejected('wrong_frame',lambda r,d:r[0].update(frame_id=7))
    rejected('unsafe_case_path',lambda r,d:r[0].update(case='../outside'))
    rejected('wrong_byte_count',lambda r,d:r[0].update(bytes=4))
    def nan_content(r,d):
        q=next(x for x in r if x['kind']=='bridge_input');v=np.frombuffer(d[q['file']],dtype='<f4').copy();v[0]=np.nan;d[q['file']]=v.tobytes()
    rejected('nonfinite_bridge',nan_content)
    # Simulate the exact early-stop boundary we need to detect: new caller but stale Input0.
    partial=[r for r in records if r['invocation']==0 or (r['invocation']==1 and r['kind'] in ('caller_input','input0_output'))]
    partial=copy.deepcopy(partial);pr=copy.deepcopy(raw)
    stale=next(r for r in partial if r['invocation']==1 and r['kind']=='input0_output')
    pr[stale['file']]=(a.reference/'S11_01_308.input.f32').read_bytes();stale['matches_expected']=False
    stop=a.output/'synthetic-input0-stale-stop';emit(stop,partial,pr)
    report=api['inspect_partial'](stop,a.reference)
    assert report['first_mismatch']==dict(invocation=1,frame_id=7,kind='input0_output')
    (stop/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    tests.append(dict(case='partial_stale_Input0_localized',rejected=True,reason='Correctly localized mismatch before bridge/NPU records'))
    # A caller write/read mismatch is distinguished from the Input0 boundary.
    changed=copy.deepcopy(single[:1]);cr=copy.deepcopy(raw);q=changed[0];q['matches_expected']=False
    v=bytearray(cr[q['file']]);v[0]^=1;cr[q['file']]=bytes(v)
    caller=a.output/'synthetic-caller-mismatch-stop';emit(caller,changed,cr)
    assert api['inspect_partial'](caller,a.reference)['first_mismatch']['kind']=='caller_input'
    tests.append(dict(case='caller_mismatch_localized',rejected=True,reason='Caller readback mismatch distinguished from Input0'))
    result=dict(status='offline_content_parser_tests_passed_not_ARM',positive_paths=['Host smoke','one call','four calls'],
                malformed_or_partial_cases=len(tests),tests=tests,SDK_called=False,compiled=False,board_accessed=False,
                content_origin='Synthetic files; actual C++ Host content paths still require user ARM execution.')
    (a.output/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Content validation synthetic tests passed: Host/one/four-call positives and {len(tests)} malformed/partial cases; no ARM execution.')


if __name__=='__main__':main()
