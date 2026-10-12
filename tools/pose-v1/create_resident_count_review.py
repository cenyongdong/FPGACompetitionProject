"""Match the isolated107-call diagnostic contract; retain the old103 reviewer."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'tools/pose-v1/review_model_only_counts.py';text=p.read_text(encoding='utf-8')
assert 'len(counts)<=824' in text
text=text.replace('pose_producer_count_selftest','pose_resident_producer_selftest').replace("'producer_selftest_sha256'","'resident_producer_selftest_sha256'").replace('824','856')
out=root/'tools/pose-v1/review_resident_counts.py';assert not out.exists();out.write_text(text,encoding='utf-8',newline='\n')
