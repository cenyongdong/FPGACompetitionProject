"""Procise ICAP and PL-only BOOT packaging after routed review; no board access."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r2'
W=R/'.local/hdmi-live-20261017-r1'
OLD=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
sys.path.insert(0,str(R/'tools/pose-v1'))
from inspect_selected_boot import bit_payload
def digest(data):return hashlib.sha256(data).hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def procise(stage,code):
 out=E/stage;work=W/stage;out.mkdir(exist_ok=False);work.mkdir(exist_ok=False)
 code=code.replace('@@WORK@@',work.as_posix())
 (out/'stage.tcl').write_text(code,encoding='ascii');(work/'stage.tcl').write_text(code,encoding='ascii')
 tool=Path('C:/FudanMicro/Procise');env=os.environ.copy()
 env.update(APP_DIR=str(tool),ICTIME_HOME=str(tool),FMSH_DB=str(tool/'db'),TCL_LIBRARY=str(tool/'tcl8.4'))
 env['PATH']=str(tool/'dll')+';'+env['PATH'];start=time.monotonic();timed=False
 with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
  p=subprocess.Popen([str(tool/'bin/procise.exe'),'stage.tcl'],cwd=work,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  dump(out/'owned-process.json',{'pid':p.pid,'budget_seconds':180,'work':str(work)})
  try:p.wait(timeout=180)
  except subprocess.TimeoutExpired:
   timed=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20)
   (out/'cleanup.txt').write_bytes(k.stdout+k.stderr);p.wait(timeout=20)
 result={'exit':p.returncode,'seconds':time.monotonic()-start,'budget':180,'timeout':timed,'board_operation':False}
 dump(out/'execution.json',result)
 assert p.returncode==0 and not timed,result
 return out,work,result
mode=sys.argv[1];assert mode in ['icap','boot','bundle']
assert json.loads((E/'monitor-v2-reports/review.json').read_text())['bit_generation_prerequisite_pass']
if mode=='icap':
 assert json.loads((E/'monitor-v2-bit/execution.json').read_text())['exit']==0
 source=W/'reference/fpai_demo_vivado.runs/impl_ai_monitor_v2/ai7030_edif_top.bit'
 code='''if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {INPUT} {@@WORK@@/ai-monitor-v2_disable_icap.bit} -disable_icap
 puts "AI_MONITOR_ICAP_COMPLETE_OFFLINE"
} result]} {puts "AI_MONITOR_ICAP_FAILED $result";exit 1}
exit
'''.replace('INPUT',source.as_posix())
 raw=source.read_bytes();out,work,execution=procise('monitor-v2-icap',code)
 patched=(work/'ai-monitor-v2_disable_icap.bit').read_bytes()
 assert digest(source.read_bytes())==digest(raw)
 payload,header=bit_payload(patched)
 assert 'Patched=DISABLE_ICAP' in header['a']
 baseline=(OLD/'rollback/ai7030_top_disable_icap.bit').read_bytes()
 assert digest(baseline)=='6818b7f8dea8e0f9dbda1b0d11127255ee1ba8876326bc7708a633641784f72e'
 base_payload,_=bit_payload(baseline);assert payload!=base_payload
 (out/'ai-monitor-v2.bit').write_bytes(raw);(out/'ai-monitor-v2_disable_icap.bit').write_bytes(patched)
 dump(out/'review.json',{'Procise_execution':execution,'raw_sha256':digest(raw),'patched_sha256':digest(patched),
  'patched_bytes':len(patched),'payload_sha256':digest(payload),'payload_bytes':len(payload),'payload_differs_from_original':True,'header':header})
elif mode=='boot':
 patch=json.loads((E/'monitor-v2-icap/review.json').read_text())
 rollback=json.loads((OLD/'rollback-identity.json').read_text(encoding='utf-8'))
 source=Path(rollback['source_directory']);original=(source/'BOOT.bin').read_bytes()
 assert digest(original)==rollback['BOOT_sha256']=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
 control=json.loads((OLD/'boot-control-utf8-r2/inputs.json').read_text(encoding='utf-8'))
 work=W/'monitor-v2-boot';assert not work.exists()
 # Procise stage creates the work directory; immutable inputs live in a sibling.
 inputs=W/'monitor-v2-boot-inputs';inputs.mkdir(exist_ok=False);ids={}
 for name in ['FSBL251210_ddr400_demo.out','bl31.elf','u-boot']:
  data=(source/name).read_bytes();assert digest(data)==control[name]['sha256'],name
  (inputs/name).write_bytes(data);ids[name]={'sha256':digest(data),'bytes':len(data),'source':str(source/name)}
 candidate=E/'monitor-v2-icap/ai-monitor-v2_disable_icap.bit'
 bit=candidate.read_bytes();assert digest(bit)==patch['patched_sha256']
 (inputs/'ai7030_top_disable_icap.bit').write_bytes(bit)
 bif='''//arch = fmql; split = false; format = BIN
the_ROM_image:
{
 [bootloader, destination_device = ps]@/FSBL251210_ddr400_demo.out
 [destination_device = pl]@/ai7030_top_disable_icap.bit
 [destination_cpu = apu_0, destination_device = ps]@/bl31.elf
 [destination_cpu = apu_0, destination_device = ps]@/u-boot
 [fsbl_config]apu_x32
}
'''.replace('@',inputs.as_posix())
 (inputs/'candidate.bif').write_text(bif,encoding='ascii')
 code='if {[catch {\n create_boot_image {'+(inputs/'candidate.bif').as_posix()+'} {@@WORK@@/BOOT-ai-monitor-v2.bin} -fmql\n puts "AI_MONITOR_BOOT_OFFLINE_COMPLETE"\n} result]} {puts "AI_MONITOR_BOOT_FAILED $result";exit 1}\nexit\n'
 out,work,execution=procise('monitor-v2-boot',code)
 (out/'candidate.bif').write_text(bif,encoding='ascii');dump(out/'inputs.json',ids)
 new=(work/'BOOT-ai-monitor-v2.bin').read_bytes();offset=rollback['BOOT_PL_offset_bytes'];end=offset+rollback['BOOT_PL_bytes']
 payload,_=bit_payload(bit);swapped=b''.join(new[i:i+4][::-1] for i in range(offset,end,4))
 result={'bytes':len(new),'sha256':digest(new),'original_sha256':digest(original),'PL_offset':offset,'PL_bytes':end-offset,
  'all_bytes_outside_PL_identical':len(new)==len(original) and new[:offset]==original[:offset] and new[end:]==original[end:],
  'PL_matches_candidate_after_word_swap':swapped[:len(payload)]==payload,
  'padding_identical':new[offset+len(payload):end]==original[offset+len(payload):end],
  'differing_PL_bytes':sum(a!=b for a,b in zip(original[offset:end],new[offset:end])),
  'candidate_bit_sha256':digest(bit),'deployed':False,'rebooted':False}
 (out/'BOOT-ai-monitor-v2.bin').write_bytes(new);dump(out/'review.json',result)
 assert result['all_bytes_outside_PL_identical'] and result['PL_matches_candidate_after_word_swap'] and result['padding_identical'] and result['differing_PL_bytes']>0,result
else:
 out=E/'controlled-startup-monitor-v2';out.mkdir(exist_ok=False)
 boot=json.loads((E/'monitor-v2-boot/review.json').read_text())
 assert boot['all_bytes_outside_PL_identical'] and boot['PL_matches_candidate_after_word_swap']
 rollback=json.loads((OLD/'rollback-identity.json').read_text(encoding='utf-8'))
 items=[(E/'monitor-v2-boot/BOOT-ai-monitor-v2.bin','BOOT-ai-monitor-v2.bin',boot['sha256']),
        (Path(rollback['source_directory'])/'BOOT.bin','BOOT-original.bin',rollback['BOOT_sha256']),
        (E/'monitor-v2-icap/ai-monitor-v2_disable_icap.bit','ai-monitor-v2_disable_icap.bit',boot['candidate_bit_sha256']),
        (E/'build-monitor-probe/ai_dma_probe','ai_dma_probe',json.loads((E/'build-monitor-probe/result.json').read_text())['binary_sha256'])]
 manifest={}
 for source,name,expected in items:
  data=source.read_bytes();assert digest(data)==expected,name
  (out/name).write_bytes(data);manifest[name]={'source':str(source),'bytes':len(data),'sha256':expected}
 dump(out/'manifest.json',manifest)
print('Offline '+mode+' completed; no deployment or reboot')
