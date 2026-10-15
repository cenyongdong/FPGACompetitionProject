from pathlib import Path
import hashlib,json,shutil,difflib
R=Path('D:/FPGACompetitionProject');E=R/'tools/pose-v1/evidence/hdmi-split-20261015-r1'
src=R/'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display/uihdmitx.v'
dst=R/'FPGA/hdmi_candidate/rtl/display/uihdmitx.v'
old=src.read_bytes();assert old.count(b'.txdata("1111100000")')==2
assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
new=old.replace(b'.txdata("1111100000")',b".txdata(10'b1111100000)")
new=new.replace(b'// -- serialization of "1111100000"',b"// -- serialization of 10'b1111100000")
dst.write_bytes(new)
assert b'.txdata("1111100000")' not in new
assert new.count(b".txdata(10'b1111100000)")==2
shutil.copyfile(src,E/'uihdmitx.original.v');shutil.copyfile(dst,E/'uihdmitx.fixed.v')
diff=''.join(difflib.unified_diff(old.decode('latin1').splitlines(True),new.decode('latin1').splitlines(True),fromfile='reference/uihdmitx.v',tofile='candidate/uihdmitx.v'))
(E/'clock-literal.patch').write_text(diff,encoding='latin1')
(E/'clock-literal-origin.json').write_text(json.dumps({'original':str(src),'candidate':str(dst),
 'original_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),
 'functional_edits':2,'branches':['UFAMILY','7FAMILY'],'reference_unchanged':src.read_bytes()==old,
 'original_bit_pattern':format(int.from_bytes(b'1111100000','big')&1023,'010b'),
 'corrected_bit_pattern':'1111100000','model_or_BOOT_modified':False},indent=2)+'\n')
print('Fixed both serializer-clock constants in isolated uihdmitx.v; reference bytes unchanged')
