"""Create a reviewable local BOOT candidate after byte-identical control; never deploy."""
from pathlib import Path
import hashlib,json,shutil,os,subprocess,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
control=json.loads((E/'boot-control-utf8-r2/result.json').read_text())
assert control['byte_identical_to_selected_BOOT'] is True
W=R/'.local/hdmi-board-reference-20261016-r1/boot-candidate';W.mkdir(exist_ok=False)
D=E/'boot-candidate';D.mkdir(exist_ok=False)
C=R/'.local/hdmi-board-reference-20261016-r1/boot-control-utf8-r2'
for name in ['FSBL251210_ddr400_demo.out','bl31.elf','u-boot']:shutil.copyfile(C/name,W/name)
candidate=E/'released-reference-products/ai7030_edif_top_disable_icap.bit'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='ab9af4b8679a8f4bbe958d4dadbc78b81156da4a3b5a67c6510c9d1269befb78'
shutil.copyfile(candidate,W/'ai7030_edif_top_disable_icap.bit')
bif=(C/'control.bif').read_text().replace(C.as_posix(),W.as_posix()).replace('ai7030_top_disable_icap.bit','ai7030_edif_top_disable_icap.bit')
(W/'candidate.bif').write_text(bif,encoding='ascii');(D/'candidate.bif').write_text(bif,encoding='ascii')
code='create_boot_image {'+(W/'candidate.bif').as_posix()+'} {'+(W/'BOOT-reference-test.bin').as_posix()+'} -fmql\nputs "OFFLINE_CANDIDATE_COMMAND_RETURNED"\nexit\n'
(D/'build.tcl').write_text(code,encoding='ascii')
P=Path('C:/FudanMicro/Procise');env=os.environ.copy();env.update(APP_DIR=str(P),TCL_LIBRARY=str(P/'tcl8.4'),ICTIME_HOME=str(P),FMSH_DB=str(P/'db'));env['PATH']=str(P/'dll')+';'+env['PATH']
t=time.monotonic()
with (D/'stdout.log').open('wb') as out,(D/'stderr.log').open('wb') as err:
 p=subprocess.Popen([str(P/'bin/procise.exe'),str(D/'build.tcl')],cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True);p.wait(timeout=10)
  (D/'timeout.json').write_text(json.dumps({'budget':180,'seconds':time.monotonic()-t}));raise
output=W/'BOOT-reference-test.bin'
result={'exit':p.returncode,'seconds':time.monotonic()-t,'budget':180,'output_exists':output.exists(),'deployed':False,'rebooted':False}
if p.returncode or not output.exists():
 (D/'result.json').write_text(json.dumps(result,indent=2));raise SystemExit('Candidate build failed')
base=(C/'BOOT-control.bin').read_bytes();new=output.read_bytes()
rollback=json.loads((E/'rollback-identity.json').read_text(encoding='utf-8'))
offset=rollback['BOOT_PL_offset_bytes'];end=offset+rollback['BOOT_PL_bytes']
outside_equal=len(new)==len(base) and base[:offset]==new[:offset] and base[end:]==new[end:]
result.update(bytes=len(new),sha256=hashlib.sha256(new).hexdigest(),BOOT_PL_offset=offset,BOOT_PL_end=end,
 all_bytes_outside_PL_partition_identical=outside_equal,
 differing_PL_bytes=sum(a!=b for a,b in zip(base[offset:end],new[offset:end])),
 source_bit_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
 semantic_scope='Only the PL partition changes; original FSBL/ATF/U-Boot, headers and parameters preserved')
shutil.copyfile(output,D/output.name)
(D/'result.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(Path(__file__),D/Path(__file__).name)
print(json.dumps(result,indent=2))
assert outside_equal,'Unexpected non-PL differences; stop before deployment'
