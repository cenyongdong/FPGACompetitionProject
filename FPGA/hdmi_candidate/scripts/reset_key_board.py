"""One bounded candidate, correct F8 reset, optional passive boot witness."""
import argparse,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text())
sys.path.insert(0,'/root/hdmi-reset-calibration-20261018-r20')
import board_support as b
BASE=Path(cfg['base']);META=BASE/'metadata';PACKAGE=Path(cfg['asset_package'])
RUN=BASE/'run-1'
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-ai-read-v3.bin']['sha256']
b.CFG=cfg;b.ROOT=BASE;b.META=META;b.MOUNT=BASE/'boot-mount';b.PACKAGE=PACKAGE
b.identity_record=lambda x:dict(x,package_id=cfg['package_id'])
def save(name,value):b.save_new(META/(name+'.json'),value);return value
def read(name):return b.read_json(META/(name+'.json'))

def bind_sample(number):
 global RUN,META
 b.need(isinstance(number,int) and 1<=number<=cfg['contract']['candidate_starts_max']<=3,'Sample outside approved cap')
 RUN=BASE/('run-'+str(number));META=RUN/'metadata'
 b.ROOT=RUN;b.META=META;b.MOUNT=RUN/'boot-mount'
 return RUN
def authorize():
 a=b.read_json(BASE/'authorization.json')
 b.need(a.get('active') is True and a.get('approved_by')=='user' and a.get('package_id')==cfg['package_id'] and a.get('caps')==cfg['caps'] and a.get('physical_key')==cfg['physical_key'],'Fresh package approval absent')
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
 b.reserve(name,dict(automatic_retry=False));out=RUN/name;out.mkdir(mode=0o700,parents=True)
 start=time.monotonic()
 with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
  p=subprocess.Popen(argv(out),cwd=BASE,stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  b.save_new(META/(name+'-process.json'),dict(pid=p.pid,boot_id=b.boot_id()))
  while p.poll() is None:
   try:p.wait(timeout=25)
   except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',pid=p.pid,proc=b.proc_snapshot(p.pid))),flush=True)
 return out,dict(exit_code=p.returncode,seconds=time.monotonic()-start,boot_id=b.boot_id(),device_owners=b.owners())

def witness(phase,sequence):
 if not cfg.get('boot_witness'):return None
 r=runtime();exe=PACKAGE/'capture_boot_witness';b.verify_file(exe,cfg['files'][exe.name])
 out,result=run_child('capture-'+phase,lambda out:[str(exe),str(out/'raw.jsonl'),str(sequence),r['boot_id']])
 rows=[json.loads(x) for x in (out/'raw.jsonl').read_text().splitlines()] if (out/'raw.jsonl').exists() else []
 snapshots=[x for x in rows if x.get('event')=='boot_witness_snapshot']
 result.update(valid=False,sequence=sequence)
 if result['exit_code']==0 and len(snapshots)==1:
  words=snapshots[0]['words'];result['words']=words
  result['valid']=(len(words)==19 and words[0]==0x42545201 and bool(words[18]&128) and result['boot_id']==r['boot_id'] and not result['device_owners'])
 save('witness-'+phase,result)
 b.need(result['valid'],'Boot witness capture invalid; preserve raw values and stop')
 return result

def witness_reset_verified():
 pre=read('witness-before');post=read('witness-after');a=pre['words'];z=post['words']
 b.need(pre['valid'] and post['valid'] and pre['boot_id']==post['boot_id']==b.boot_id(),'Witness runtime changed')
 b.need(not ((a[18]|z[18])&0xf00) and not ((a[1]|z[1])&0x1e000),'Witness counter overflow: no SDK')
 # Compare raw counters rather than the user confirmation alone. A missing HP2
 # pulse is a diagnostic result and stops the conditional SDK phase.
 # A physical key operation can produce several internal edges. Require
 # observed assertion and width in both domains, not exactly one edge.
 pulses=z[13]>a[13] and z[14]>a[14] and z[16]>a[16] and z[17]>a[17]
 retained=all(z[i]>=a[i] for i in range(3,7))
 if a[1]&1:retained=retained and z[7:9]==a[7:9]
 if a[1]&2:retained=retained and z[9:11]==a[9:11]
 if a[1]&4:retained=retained and z[11:13]==a[11:13]
 return pulses and retained

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
 save(phase,result)
 if result['valid']:witness(phase,2)
 return result

def software(require_physical_reset=True):
 runtime()
 if require_physical_reset:
  b.need(read('after').get('healthy') is True,'Post-reset pure CSR not healthy: no SDK load')
  if cfg.get('boot_witness'):
   b.need(read('before').get('healthy') is True and witness_reset_verified(),'Pure startup/reset witness unhealthy: no SDK load')
   b.need(not ((read('witness-before')['words'][1]|read('witness-after')['words'][1])&8),'Earlier ready-state RVALID without observed AR: preserve history, no SDK')
 else:
  b.need(cfg['caps']['PL_KEY1_SW6_pulses']==0 and cfg['contract']['physical_reset_max']==0,'Package does not authorize keyless startup observation')
  b.need(read('before').get('healthy') is True and cfg.get('boot_witness'),'Healthy startup CSR/history required before SDK')
  witness_before=read('witness-before');w=witness_before['words']
  b.need(witness_before['valid'] and witness_before['boot_id']==b.boot_id() and w[14]>0 and w[17]>0 and not (w[18]&0xf00) and not (w[1]&0x1e008),'Startup HP2 reset/history gate failed: no SDK')
 assets=cfg['software_assets'];supervisor=assets['startup_init_supervisor']['path'];child=assets['startup_sdk_child']['path']
 out,result=run_child('software',lambda out:[supervisor,str(out/'trace.jsonl'),child])
 rows=[]
 if (out/'trace.jsonl').exists():rows=[json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines()]
 snaps=[x for x in rows if x.get('event')=='startup_snapshot']
 result.update(passed=False,snapshots=snaps,SDK_Open_attempts=sum(x.get('event')=='before_Device_Open' for x in rows))
 expected=[('pure_before_library',4),('library_load',6),('Device_Open',8),('idle_after_Open',10),('Device_Close_and_unload',12)]
 if result['exit_code']==0:
  result['passed']=not result['device_owners'] and [(x['phase'],x['sequence']) for x in snaps]==expected and result['SDK_Open_attempts']==1 and any(x.get('event')=='SOFTWARE_INIT_OBSERVATION_COMPLETE' for x in rows)
 save('software',result)
 if cfg.get('boot_witness') and snaps and not result['device_owners']:
  witness('software',snaps[-1]['sequence'])
 return result

def main(stage):
 key=cfg.get('physical_key',{})
 b.need(HERE==BASE and BASE.parent==Path('/root') and key.get('name')=='PL_KEY1' and key.get('reference')=='SW6' and key.get('pin')=='F8','Wrong package location/key')
 if stage=='audit':return b.audit(ORIGINAL)
 a=authorize()
 if stage=='prepare':
  audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id'])
  b.need(PACKAGE.is_dir() and not PACKAGE.is_symlink(),'Unsafe package directory')
  for name,source in cfg.get('asset_reuse',{}).items():
   target=PACKAGE/name;b.verify_file(Path(source),cfg['files'][name])
   if not target.exists():shutil.copyfile(source,target)
  b.checked_backup()
  for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
  for name in ('ai_preopen_monitor','capture_boot_witness'):
   if name in cfg['files']:os.chmod(PACKAGE/name,0o700)
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
