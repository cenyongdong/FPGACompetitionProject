"""Retain object/count verification; adapt only the new seven-task ledger."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for src,dest in [('review_tensor_objects.py','review_model_only_objects.py'),('review_tensor_counter.py','review_model_only_counts.py')]:
    s=(root/'tools/pose-v1'/src).read_text(encoding='utf-8');assert s.count("len(ledger['tasks'])==8")==1;s=s.replace("len(ledger['tasks'])==8","len(ledger['tasks'])==7")
    p=root/'tools/pose-v1'/dest;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
