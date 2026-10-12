"""Generate an isolated evidence reviewer with the frozen typed numerical rules."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'tools/pose-v1/review_typed_scratch.py').read_text(encoding='utf-8')
s=s.replace('from review_typed_build import','from review_position_build import').replace("choices=['baseline','contracts','static','dynamic','vpu']","choices=['baseline','contracts','dynamic','vpu']")
s=s.replace("p.add_argument('--native',type=Path);","p.add_argument('--native',type=Path);p.add_argument('--position-native',type=Path);")
s=s.replace("typed_binary_sha256=b['typed_binary_sha256']","typed_binary_sha256=b['typed_binary_sha256'],position_binary_sha256=b['position_binary_sha256']")
s=s.replace("('pose_typed_scratch_check','typed_binary_sha256')","('pose_position_scratch_check','position_binary_sha256'),('pose_plddr_position_selftest','position_selftest_sha256')")
s=s.replace("'typed_baseline_exact_main_Host107_reused'","'position_baseline_exact_main_Host107_reused'").replace("status='typed_stage_passed'","status='position_stage_passed'")
s=s.replace("'tools/pose-v1/run-typed-scratch.sh'","'tools/pose-v1/run-position-scratch.sh'")
s=s.replace("g.sha(r/'pose_typed_scratch_check')==b['typed_binary_sha256']","g.sha(r/'pose_position_scratch_check')==b['position_binary_sha256']")
needle="    if a.stage=='baseline':"
assert s.count(needle)==1
s=s.replace(needle,"""    if a.position_native:
        pn=a.position_native;assert g.load(pn/'stdout.json')==dict(status='passed',refusals=12,legal_position=True,SDK_device=False) and not (pn/'stderr.log').read_bytes() and (pn/'exit.txt').read_text().strip()=='0';report['Native_position_refusals']=12
    assert m['plddr_position']['manager_audit_sha256']==g.sha(g.ROOT/'tools/pose-v1/evidence/plddr-position-20261010-r1/manager.acceptance.json')
"""+needle)
needle="contract(r/'results');report.update(ARM_refusals=8,SDK_device=False)"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n            assert g.load(r/'position.stdout.json')==dict(status='passed',refusals=12,legal_position=True,SDK_device=False) and not (r/'position.stderr.log').read_bytes() and (r/'position.exit.txt').read_text().strip()=='0' and g.sha(r/'pose_plddr_position_selftest')==b['position_selftest_sha256'];report['ARM_position_refusals']=12")
needle="            life=rows(out/'lifecycle.jsonl');"
assert s.count(needle)==1
s=s.replace(needle,"""            pos=g.load(out/'sdk/position.json');assert pos['position_controlled'] and pos['prefix_bytes']==96*1024*1024 and pos['prefix_read_write_copy_calls']==0 and not pos['explicit_address_allocation']
            assert pos['source_lower']==64*1024*1024 and pos['source_upper_exclusive']==128*1024*1024
            snaps=[g.load(out/'sdk'/name) for name in ['manager-before.json','manager-prefix.json','manager-allocated.json','manager-released.json']]
            assert [len(x['chunks']) for x in snaps]==[0,1,4,0] and all(x['start']==4096 and x['bytes']==4294963200 and x['manager_type']=='icraft::xrt::DefaultMemManagerNode' for x in snaps)
            blocks=snaps[2]['chunks'];assert len(set(x['identity'] for x in blocks))==4 and not (out/'sdk/release.error.txt').exists()
            for i,x in enumerate(blocks):
                assert x['region_owned'] and x['address']>=4096 and x['bytes']>0 and x['address']+x['bytes']<=4294967296
                for y in blocks[i+1:]:assert x['address']+x['bytes']<=y['address'] or y['address']+y['bytes']<=x['address']
            prefix=next(x for x in blocks if x['identity']==pos['prefix_chunk_identity']);assert prefix==snaps[1]['chunks'][0] and prefix['bytes']==pos['prefix_bytes'] and prefix['address']==pos['prefix_address']
            for x in meta['sources']:
                assert pos['source_lower']<=x['address'] and x['address']+x['bytes']<=pos['source_upper_exclusive']
                c=next(v for v in blocks if v['identity']==x['chunk_identity']);assert c['address']==x['address'] and c['bytes']==x['bytes']
            assert next(x['bytes'] for x in blocks if x['address']==meta['padding_address'])==32
            report.update(public_owned_position_verified=True,source_addresses=[x['address'] for x in meta['sources']],SDK_chunks_released=4,prefix_data_operations=0)
"""+needle)
out=root/'tools/pose-v1/review_position_scratch.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
