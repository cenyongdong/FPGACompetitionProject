"""Use actual failed phase/case identity; old103 helpers remain frozen."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'tools/pose-v1/compare_invocation_host_frame.py').read_text(encoding='utf-8')
start=s.index('        identity=g.load(out/\'failed-host-inputs/failure.json\')');end=s.index('\n    assert identity',start)
s=s[:start]+'''        identity=g.load(out/'failed-host-inputs/failure.json')
        attempt=g.load(out/'failed-attempt/identity.json');case=attempt['case']
        assert attempt['frame_id']==index['frame_id'] and attempt['invocation']==index['invocation']
        assert (out/'failed-attempt/raw-payload.bin').read_bytes()==(a.package/'inputs'/(case+'.csi')).read_bytes()[32:]'''+s[end:]
p=root/'tools/pose-v1/compare_picture_host_frame.py';assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
