"""Prepare isolated runtime and Native contracts from the frozen resident tools."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
def put(rel,s):p=root/rel;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
s=(root/'tools/pose-v1/run-resident-sequence.sh').read_text(encoding='utf-8')
s=s.replace('contracts / resident','contracts / picture').replace('resident) previous','picture) previous').replace('pose_resident_sequence_check','pose_picture_check').replace('resident_binary_sha256','picture_binary_sha256').replace('resident_baseline_exact_main_Host107_reused','picture_baseline_exact_main_Host107_reused').replace('resident_contracts_passed','picture_contracts_passed')
s=s.replace("('pose_resident_sequence_selftest','resident_selftest_sha256')","('pose_picture_sequence_selftest','picture_sequence_selftest_sha256'),('pose_picture_source_selftest','picture_source_selftest_sha256')")
s=s.replace('for name in pose_resident_sequence_selftest','for name in pose_picture_source_selftest pose_picture_sequence_selftest').replace('Single resident lifecycle','Owned picture lifecycle')
put('tools/pose-v1/run-picture.sh',s)
s=(root/'tools/pose-v1/run_resident_sequence_native.py').read_text(encoding='utf-8').replace('resident-sequence-20261010-r1','picture-20261010-r1').replace("('sequence',['resident_sequence_selftest.cpp','resident_sequence.cpp'","('sequence',['picture_sequence_selftest.cpp','picture_sequence.cpp'")
s=s.replace("for label,sources,arg in [","for label,sources,arg in [('source',['picture_source_selftest.cpp','picture_source.cpp','picture_marker.cpp'],None),")
put('tools/pose-v1/run_picture_native.py',s)
print('New runner and Native tools created; no execution.')
