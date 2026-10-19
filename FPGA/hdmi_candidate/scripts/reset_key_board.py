"""Bounded r9 reuse: correct F8/PL_KEY1 reset, then one conditional SDK Open."""
import argparse,json,os,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text())
sys.path.insert(0,'/root/hdmi-reset-calibration-20261018-r20')
import board_support as b
BASE=Path(cfg['base']);META=BASE/'metadata';PACKAGE=Path(cfg['asset_package'])
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-ai-read-v3.bin']['sha256']
b.CFG=cfg;b.ROOT=BASE;b.META=META;b.MOUNT=BASE/'boot-mount';b.PACKAGE=PACKAGE
b.identity_record=lambda x:dict(x,package_id=cfg['package_id'])
def save(name,value):b.save_new(META/(name+'.json'),value);return value
def read(name):return b.read_json(META/(name+'.json'))
def authorize():
 a=b.read_json(BASE/'authorization.json')
 b.need(a.get('active') is True and a.get('approved_by')=='user' and a.get('package_id')==cfg['package_id'] and a.get('caps')==cfg['caps'] and a.get('physical_key')==cfg['physical_key'],'Fresh r21 approval absent')
 return a
def runtime():
 r=read('restore');b.need(r['passed'] and r['BOOT_sha256']==ORIGINAL and r['boot_id']==b.boot_id(),'Original boot file not restored in this runtime')
 b.need(not b.owners(),'Device owner present');return r

def reset_kind(r):
 w=r.get('snapshot',{}).get('words',[])
 if not r.get('valid') or len(w)!=104 or w[0]!=0x41495201 or w[1]==0 or (w[2]&31)!=0x19 or w[3]!=0 or r.get('device_owners'):return None
 if any(w[8+16*c] or w[9+16*c] or w[11+16*c] for c in range(6)):return None
 if all(w[15+16*c]==0 for c in range(6)):return 'healthy_idle'
 if w[79]==w[77]==w[95]==w[93]==w[1]:return 'known_idle_return_fault'
 return None

def run_child(name,argv):
 b.reserve(name,dict(automatic_retry=False));out=BASE/'run-1'/name;out.mkdir(mode=0o700,parents=True)
 start=time.monotonic()
 with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
  p=subprocess.Popen(argv(out),cwd=BASE,stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  b.save_new(META/(name+'-process.json'),dict(pid=p.pid,boot_id=b.boot_id()))
  while p.poll() is None:
   try:p.wait(timeout=25)
   except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',pid=p.pid,proc=b.proc_snapshot(p.pid))),flush=True)
 return out,dict(exit_code=p.returncode,seconds=time.monotonic()-start,boot_id=b.boot_id(),device_owners=b.owners())

def observe(phase):
 r=runtime()
 if phase=='after':
  key=read('user-reset');attempt=read('physical-reset-attempt')
  b.need(key.get('confirmed_by')=='user' and key.get('key')=='PL_KEY1/SW6' and key.get('pulses')==1 and key.get('boot_id')==r['boot_id'] and attempt['boot_id']==r['boot_id'],'Correct one-key completion not confirmed')
 exe=PACKAGE/'ai_preopen_monitor'
 out,result=run_child('observe-'+phase,lambda out:[str(exe),str(out/'trace.jsonl')])
 initial=[]
 for line in (out/'stderr.log').read_text(errors='replace').splitlines():
  if line.startswith('PREOPEN_CSR_INITIAL '):initial.append(json.loads(line[len('PREOPEN_CSR_INITIAL '):]))
 result.update(initial_values=initial[-1] if initial else None,valid=False,healthy=False,SDK_load=False)
 if result['exit_code']==0:
  x=json.loads((out/'trace.jsonl').read_text());w=x['words'];result['snapshot']=x
  result['valid']=len(w)==104 and w[0]==0x41495201 and x['status']==0 and x['request']==x['response']==2 and result['boot_id']==r['boot_id'] and not result['device_owners']
  result['healthy']=result['valid'] and (w[2]&31)==0x19 and w[3]==0 and all(w[8+16*c]==w[9+16*c]==w[15+16*c]==0 for c in range(6))
 result['reset_sample_kind']=reset_kind(result)
 return save(phase,result)

def software():
 runtime();b.need(read('after').get('healthy') is True,'Post-reset pure CSR not healthy: no SDK load')
 assets=cfg['software_assets'];supervisor=assets['startup_init_supervisor']['path'];child=assets['startup_sdk_child']['path']
 out,result=run_child('software',lambda out:[supervisor,str(out/'trace.jsonl'),child])
 rows=[]
 if (out/'trace.jsonl').exists():rows=[json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines()]
 snaps=[x for x in rows if x.get('event')=='startup_snapshot']
 result.update(passed=False,snapshots=snaps,SDK_Open_attempts=sum(x.get('event')=='before_Device_Open' for x in rows))
 expected=[('pure_before_library',4),('library_load',6),('Device_Open',8),('idle_after_Open',10),('Device_Close_and_unload',12)]
 if result['exit_code']==0:
  result['passed']=not result['device_owners'] and [(x['phase'],x['sequence']) for x in snaps]==expected and result['SDK_Open_attempts']==1 and any(x.get('event')=='SOFTWARE_INIT_OBSERVATION_COMPLETE' for x in rows)
 return save('software',result)

def main(stage):
 b.need(HERE==BASE and str(BASE)=='/root/hdmi-reset-meter-20261019-r21','Wrong r21 location')
 if stage=='audit':return b.audit(ORIGINAL)
 a=authorize()
 if stage=='prepare':
  audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id']);b.checked_backup()
  for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
  for row in cfg['software_assets'].values():b.verify_file(Path(row['path']),row)
  host=cfg['independent_host_backup'];b.need(host['verified'] and host['sha256']==ORIGINAL and host['bytes']==7023552,'Host original backup absent')
  b.MOUNT.mkdir(mode=0o700);return save('prepare',dict(passed=True,boot_id=audit['boot_id'],reused_assets=True))
 if stage=='install':
  p=read('prepare');b.audit(ORIGINAL,p['boot_id'])
  return b.replace_boot(PACKAGE/'BOOT-ai-read-v3.bin',ORIGINAL,CANDIDATE,'install','install.json')
 if stage in ('candidate-reboot','fallback-reboot'):
  candidate=stage=='candidate-reboot';r=read('install') if candidate else runtime();b.audit(CANDIDATE if candidate else ORIGINAL,r['boot_id'])
  name='candidate-1' if candidate else 'original-fallback';save(name+'-attempt',dict(boot_id=b.boot_id(),automatic_retry=False,time_unix=time.time()))
  p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  return dict(command_issued=True,helper_pid=p.pid,boot_id=b.boot_id())
 if stage=='restore':
  b.need(read('candidate-1-attempt')['boot_id']!=b.boot_id(),'No new candidate boot');b.audit(CANDIDATE)
  return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
 if stage=='probe':return observe('before')
 if stage=='request-reset':
  r=runtime();kind=reset_kind(read('before'));b.need(kind is not None,'No safe idle baseline: no physical key')
  return save('physical-reset-attempt',dict(boot_id=r['boot_id'],key='PL_KEY1/SW6',pin='F8',pulses_max=1,baseline_kind=kind,SDK_load=False))
 if stage=='post-reset':return observe('after')
 if stage=='software':return software()
 if stage=='close':
  b.need(read('restore')['boot_id']!=b.boot_id(),'Candidate runtime still active');read('original-fallback-attempt');audit=b.audit(ORIGINAL);save('final-audit',audit)
  a.update(active=False,remaining_candidate_starts=0,remaining_original_fallbacks=0,remaining_key_pulses=0,remaining_SDK_Open=0)
  (BASE/'authorization.json').write_text(json.dumps(a,indent=2));return dict(closed=True,boot_id=audit['boot_id'])
 raise RuntimeError('Unknown stage')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','prepare','install','candidate-reboot','restore','probe','request-reset','post-reset','software','fallback-reboot','close']);p.add_argument('--cycle',type=int,default=1);args=p.parse_args()
 try:print(json.dumps(main(args.stage),ensure_ascii=False,indent=2),flush=True)
 except BaseException:traceback.print_exc();raise SystemExit(1)
