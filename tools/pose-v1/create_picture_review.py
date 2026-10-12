"""Isolated numerical/lifetime reviewer matched to the approved picture scope."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
old=(root/'tools/pose-v1/review_resident_sequence.py').read_text(encoding='utf-8')
s=old.replace('review_resident_sequence_build_base','review_picture_build_base').replace('resident_binary_sha256','picture_binary_sha256').replace('pose_resident_sequence_check','pose_picture_check').replace('resident-three-103','picture-three-103').replace("'resident'","'picture'").replace('run-resident-sequence.sh','run-picture.sh')
s=s.replace('resident_stage_passed','picture_stage_passed').replace('resident_baseline_exact_main_Host107_reused','picture_baseline_exact_main_Host107_reused').replace('resident_contracts_passed','picture_contracts_passed').replace('resident_first_startup_failed','picture_first_startup_failed').replace('resident_content_failed','picture_content_failed')
s=s.replace("('sequence','pose_resident_sequence_selftest','resident_selftest_sha256',SEQUENCE)","('source','pose_picture_source_selftest','picture_source_selftest_sha256',SOURCE),('sequence','pose_picture_sequence_selftest','picture_sequence_selftest_sha256',SEQUENCE)")
s=s.replace('TESTS=[','SOURCE=dict(status="passed",refusals=13,calls=107,capacity=2,owns_publication=True,immutable_repeat=True,overwrite_oldest=True,coalesces_latest=True,drains_last_pending=True,owner_checked=True,SDK_device=False)\nTESTS=[')
s=s.replace('(200000000 if phase else 500000000)','500000000')
needle="                    assert v['drained'] and v['submitted']==v['returned']<1000"
assert s.count(needle)==1
s=s.replace(needle,"                    assert v['published']==v['consumed']==107 and v['queue_capacity']==2 and not v['overwritten'] and not v['coalesced'] and v['high_water']<=2\n"+needle)
s=s.replace('synthetic_VPU_only=True','synthetic_VPU_only=False,real_owned_pictures=True')
out=root/'tools/pose-v1/review_picture.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
p=root/'tools/pose-v1/run_picture_native.py';text=p.read_text(encoding='utf-8');assert '/tmp/pose-v1-mixed-20261010-resident-sequence-r1' in text;text=text.replace('/tmp/pose-v1-mixed-20261010-resident-sequence-r1','/tmp/pose-v1-mixed-20261010-picture-r1');p.write_text(text,encoding='utf-8',newline='\n')
print('New picture reviewer/Native path ready, no runtime data changed.')
