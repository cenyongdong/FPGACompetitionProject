"""Offline factory-format boot-image control; NEVER deploy or reboot."""
from pathlib import Path
import hashlib,json,shutil,os,subprocess,time,sys
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
assert sys.argv[1:]==['utf8-r2']
W=R/'.local/hdmi-board-reference-20261016-r1/boot-control-utf8-r2';W.mkdir(exist_ok=False)
D=E/'boot-control-utf8-r2';D.mkdir(exist_ok=False)
audit=json.loads((E/'rollback-identity.json').read_text(encoding='utf-8'));S=Path(audit['source_directory'])
names=['FSBL251210_ddr400_demo.out','bl31.elf','u-boot','ai7030_top_disable_icap.bit']
ids={}
for name in names:
 src=S/name;dst=W/name;shutil.copyfile(src,dst)
 ids[name]={'source':str(src),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size}
(D/'inputs.json').write_text(json.dumps(ids,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
bif='''//arch = fmql; split = false; format = BIN
the_ROM_image:
{
 [bootloader, destination_device = ps]@/FSBL251210_ddr400_demo.out
 [destination_device = pl]@/ai7030_top_disable_icap.bit
 [destination_cpu = apu_0, destination_device = ps]@/bl31.elf
 [destination_cpu = apu_0, destination_device = ps]@/u-boot
 [fsbl_config]apu_x32
}
'''.replace('@',W.as_posix())
(W/'control.bif').write_text(bif,encoding='ascii');(D/'control.bif').write_text(bif,encoding='ascii')
script='create_boot_image {'+(W/'control.bif').as_posix()+'} {'+(W/'BOOT-control.bin').as_posix()+'} -fmql\nputs "OFFLINE_CONTROL_COMMAND_RETURNED"\nexit\n'
(D/'build.tcl').write_text(script,encoding='ascii')
P=Path('C:/FudanMicro/Procise');env=os.environ.copy();env.update(APP_DIR=str(P),TCL_LIBRARY=str(P/'tcl8.4'),ICTIME_HOME=str(P),FMSH_DB=str(P/'db'));env['PATH']=str(P/'dll')+';'+env['PATH']
t=time.monotonic()
with (D/'stdout.log').open('wb') as out,(D/'stderr.log').open('wb') as err:
 p=subprocess.Popen([str(P/'bin/procise.exe'),str(D/'build.tcl')],cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True);p.wait(timeout=10)
  (D/'timeout.json').write_text(json.dumps({'budget':180,'elapsed':time.monotonic()-t})+'\n');raise
output=W/'BOOT-control.bin';source_boot=S/'BOOT.bin'
result={'exit':p.returncode,'seconds':time.monotonic()-t,'budget':180,'source_BOOT_sha256':audit['BOOT_sha256'],
 'control_exists':output.exists(),'deployed':False,'rebooted':False}
if output.exists():
 result.update(control_bytes=output.stat().st_size,control_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
               byte_identical_to_selected_BOOT=output.read_bytes()==source_boot.read_bytes())
 shutil.copyfile(output,D/output.name)
(D/'result.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(Path(__file__),D/Path(__file__).name)
print(json.dumps(result));print((D/'stdout.log').read_text(errors='replace')[-3000:])
if p.returncode or not output.exists():raise SystemExit('Offline control build failed; preserve evidence, no deploy')
