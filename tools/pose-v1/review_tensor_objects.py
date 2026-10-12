"""Independent object/type/ownership alignment against unchanged owned shadows."""
import argparse,json,struct,collections
from pathlib import Path
import mixed_validation_gate as g
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    b=g.load(a.build/'build-result.json');binary=a.build/'pose_tensor_identity_selftest';assert g.sha(binary)==b['tensor_identity_selftest_sha256'] and struct.unpack_from('<H',binary.read_bytes(),18)[0]==183
    report=dict(status='tensor_identity_checked',selftest_sha256=g.sha(binary),normal_device_reads_added=0)
    if a.native:
        normal=rows(a.native/'normal/objects.jsonl');changed=rows(a.native/'changed/objects.jsonl')
        assert len(normal)==len(changed)==2 and not any(v['error'] for v in normal)
        assert changed[-1]['error']=='Identity changed across copy' and changed[0]['source']['region_object']==2 and changed[1]['source']['region_object']==9
        report.update(Native_refusals=17,partial_identity_saved=True)
    if a.results:
        r=a.results;out=r/'results';g.verify(r)
        if (r/'identity-contracts.stdout.log').exists():
            assert g.load(r/'identity-contracts.stdout.log')==dict(status='passed',refusals=17,partial_identity_saved=True,normal_device_reads_added=0,SDK_device=False)
            assert (r/'identity-contracts.exit.txt').read_text().strip()=='0' and not (r/'identity-contracts.stderr.log').read_bytes()
            assert g.sha(r/'pose_tensor_identity_selftest')==g.sha(binary)
            changed=rows(r/'identity-contracts/changed/objects.jsonl');assert len(changed)==2 and changed[-1]['error']=='Identity changed across copy'
            report.update(status='Host_tensor_identity_contracts_passed',ARM_refusals=17,device_opened=False)
        else:
            data=rows(out/'tensor-identities/objects.jsonl');assert data and len(data)<=2048
            meta=rows(out/'copy-observations/metadata.jsonl');shadows={(x['frame_id'],x['invocation'],x['op_id'],x['slot']):x for x in meta if x['kind']=='post_copy_Host_shadow'}
            assert len(data)==2*len(shadows);source_regions=set();source_chunks=set();source_devices=set();host_regions=set();shapes={};destinations=[]
            for before,after in zip(data[::2],data[1::2]):
                key=tuple(after[k] for k in ('frame_id','invocation','op_id','slot'));shadow=shadows[key]
                assert before['point']=='before_copy' and after['point']=='after_copy' and all(before[k]==after[k] for k in ('frame_id','invocation','op_id','slot','source','destination','same_region','same_device'))
                assert not before['error'] and not after['error'] and not after['device_data_read_added']
                assert before['time_ns']<=shadow['copy_begin_ns']<=shadow['copy_end_ns']<=shadow['shadow_end_ns']<=after['time_ns']
                s=after['source'];d=after['destination']
                for value in (s,d):
                    assert all(value[k]>0 for k in ('tensor_object','region_object','chunk_object','device_object','address_identity','bytes'))
                    assert value['owner_matches'] and value['declared_matches'] and value['offset']+value['bytes']<=value['capacity']
                    typ=value['actual_type'];assert typ==value['declared_type'] and typ['FP32'] and typ['bytes']==value['bytes']
                    size=4
                    for dim in typ['shape']:assert dim>0;size*=dim
                    assert size==value['bytes'] and len(typ['layout'])==len(typ['shape'])
                    assert typ['layout']=='*'*(len(typ['shape'])-1)+'C'
                    for dist in typ['distributions']:
                        assert dist['uvalue']==0 and len(set(dist['axes']))==len(dist['axes']) and dist['axes'];extent=1
                        for axis in dist['axes']:assert 0<=axis<len(typ['shape']);extent*=typ['shape'][axis]
                        assert len(dist['valid_mask'])==extent and set(dist['valid_mask'])=={'1'}
                assert s['actual_type']==d['actual_type'] and s['bytes']==shadow['bytes']==d['bytes']
                assert s['pointer'] in ('ADDR','BOTH') and d['pointer']=='CPTR' and not after['same_region'] and not after['same_device']
                assert s['address_identity']==shadow['source_address'] and s['offset']==shadow['source_offset'] and s['capacity']==shadow['source_capacity']
                assert d['address_identity']==shadow['Host_CPTR'] and d['chunk_object']==shadow['Host_chunk'] and d['offset']==shadow['Host_offset'] and d['capacity']==shadow['Host_capacity']
                source_regions.add(s['region_object']);source_chunks.add(s['chunk_object']);source_devices.add(s['device_object']);host_regions.add(d['region_object']);destinations.append(d['address_identity'])
                shapes[f"{after['op_id']}.{after['slot']}"]=s['actual_type']
            ledger=g.load(out/'persistence-ledger.json');assert len(ledger['tasks'])==8 and all(x['saved'] for x in ledger['tasks'] if x['name']!='complete-results') and any(x['name']=='tensor-object-identities' and x['saved'] for x in ledger['tasks'])
            report.update(status='actual_model_objects_types_and_shadows_matched',rows=len(data),copied_inputs=len(shadows),source_region_objects=sorted(source_regions),source_device_objects=sorted(source_devices),source_chunk_objects=len(source_chunks),Host_region_objects=sorted(host_regions),unique_Host_destination_addresses=len(set(destinations)),actual_types=shapes,object_changed_across_copy=False,root_cause_proven=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='actual_types'}))
if __name__=='__main__':main()
