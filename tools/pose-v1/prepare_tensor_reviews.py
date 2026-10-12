"""Adapt old independent persistence review only for the eighth identity task."""
from pathlib import Path
root=Path(__file__).parent
for source,target in [('review_producer_invocation.py','review_tensor_invocation.py'),('review_producer_count_evidence.py','review_tensor_counter.py')]:
    s=(root/source).read_text(encoding='utf-8');assert "len(ledger['tasks'])==7" in s
    s=s.replace("len(ledger['tasks'])==7","len(ledger['tasks'])==8")
    if source=='review_producer_invocation.py':s=s.replace("'192-producer-counts','Engine-evidence'","'192-producer-counts','tensor-object-identities','Engine-evidence'")
    if source=='review_failed_producer_count.py':s=s.replace('review_producer_count_stage','review_tensor_identity_r3_stage')
    p=root/target;assert not p.exists();p.write_text(s,encoding='utf-8')
