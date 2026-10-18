"""Copy the frozen v2 reference for passive read-path observation development."""
from pathlib import Path
import json,hashlib,shutil,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
OLD=R/'.local/hdmi-live-20261017-r1/reference';NEW=R/'.local/hdmi-live-20261017-r3/reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not NEW.exists();begin=time.monotonic()
    frozen=json.loads((R/'tools/pose-v1/evidence/hdmi-live-20261017-r2/monitor-v2-constraints/review.json').read_text())['source_sha256']
    for name,expected in frozen.items():assert sha(OLD/name)==expected,('Frozen reference changed',name)
    copied=[0,0]
    def copy(src,dst):
        if time.monotonic()-begin>180:raise TimeoutError('Copy budget, preserve partial new reference')
        shutil.copy2(src,dst);copied[0]+=1;copied[1]+=Path(src).stat().st_size
        if copied[0]%500==0:print(json.dumps({'copied_files':copied[0],'seconds':time.monotonic()-begin}),flush=True)
        return dst
    def ignore(path,names):
        omit={'.Xil','fpai_demo_vivado.sim','fpai_demo_vivado.hw','.git'}
        if Path(path).name=='fpai_demo_vivado.runs':omit|={n for n in names if n=='synth_1' or not n.endswith('_synth_1')}
        return [n for n in names if n in omit or n.endswith(('.jou','.backup.log'))]
    shutil.copytree(OLD,NEW,copy_function=copy,ignore=ignore)
    remapped=[]
    for p in NEW.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.xpr','.tcl','.bat','.xml','.xci','.xdc','.log','.rpt'}:continue
        try:s=p.read_text(encoding='utf-8')
        except UnicodeError:continue
        out=s.replace(OLD.as_posix(),NEW.as_posix()).replace(str(OLD),str(NEW))
        if out!=s:p.write_text(out,encoding='utf-8');remapped.append(p.relative_to(NEW).as_posix())
    # Functional RTL must be identical at this boundary; later minimal changes
    # are separately reviewed and never overwrite the old reference or evidence.
    identity=[]
    for p in (OLD/'rtl').rglob('*'):
        if not p.is_file():continue
        n=p.relative_to(OLD);assert sha(p)==sha(NEW/n),n;identity.append({'path':n.as_posix(),'sha256':sha(p)})
    result={'copied_files':copied[0],'copied_bytes':copied[1],'seconds':time.monotonic()-begin,
        'old_reference':str(OLD),'new_reference':str(NEW),'frozen_sources_checked':len(frozen),
        'RTL_before_any_new_integration':identity,'path_remapped_files':remapped,'board_access':False}
    (E/'read-reference-copy.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('RTL_before_any_new_integration','path_remapped_files')}),flush=True)

if __name__=='__main__':main()
