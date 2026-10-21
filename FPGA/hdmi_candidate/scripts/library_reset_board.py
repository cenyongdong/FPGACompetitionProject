"""r22: reuse r9 and existing SDK-first probes; fault-only SW6 comparison."""
import argparse,json,os,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text())
sys.path.insert(0,'/root/hdmi-reset-calibration-20261018-r20')
import board_support as b
BASE=Path(cfg['base']);META=BASE/'metadata';PACKAGE=Path(cfg['asset_package'])
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-ai-read-v3.bin']['sha256']
b.CFG=cfg;b.PACKAGE=PACKAGE
b.identity_record=lambda x:dict(x,package_id=cfg['package_id'])

def read(name):return b.read_json(META/(name+'.json'))
def save(name,value):b.save_new(META/(name+'.json'),value);return value
def record(n,name):return b.read_json(BASE/('run-'+str(n))/'metadata'/(name+'.json'))
def bind(n):
 b.need(1<=n<=cfg['caps']['candidate_starts'],'Outside candidate cap')
 b.ROOT=BASE/('run-'+str(n));b.META=b.ROOT/'metadata';b.MOUNT=b.ROOT/'boot-mount'
def authorize():
 a=b.read_json(BASE/'authorization.json')
 b.need(a.get('active') is True and a.get('approved_by')=='user' and a.get('package_id')==cfg['package_id'] and a.get('caps')==cfg['caps'] and a.get('physical_key')==cfg['physical_key'],'Fresh r22 approval absent')
 return a
def runtime(n):
 r=record(n,'restore');b.need(r['passed'] and r['BOOT_sha256']==ORIGINAL and r['boot_id']==b.boot_id(),'Original BOOT not restored in this runtime')
 b.need(not b.owners(),'Device owner present');return r
def prior(n):
 if n==1:return cfg['board']['pre_start_boot_id']
 r=runtime(n-1);b.need(record(n-1,'software')['passed'],'Previous startup abnormal: no next sample')
 b.need(not (META/'physical-reset-attempt.json').exists(),'Reset comparison already requested: no next sample')
 return r['boot_id']
def run_child(name,argv):
 b.reserve(name,dict(automatic_retry=False));out=b.ROOT/name;out.mkdir(mode=0o700)
 start=time.monotonic()
 with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
  p=subprocess.Popen(argv(out),cwd=BASE,stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  b.save_new(b.META/(name+'-process.json'),dict(pid=p.pid,boot_id=b.boot_id()))
  while p.poll() is None:
   try:p.wait(timeout=25)
   except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',pid=p.pid,proc=b.proc_snapshot(p.pid))),flush=True)
 return out,dict(exit_code=p.returncode,seconds=time.monotonic()-start,boot_id=b.boot_id(),device_owners=b.owners())
def snapshot_valid(s):
 w=s.get('words',[])
 return len(w)==104 and w[0]==0x41495201 and w[1]>0 and (w[2]&31)==0x19 and w[3]==0
def idle_healthy(s):
 w=s.get('words',[])
 return snapshot_valid(s) and all(w[8+16*c]==w[9+16*c]==w[15+16*c]==0 for c in range(6))
def recognized_preopen_fault(result):
 snaps=result['snapshots'];events=result['events']
 if result['device_owners'] or result['exit_code']==0 or result['SDK_Open_attempts'] or len(snaps)!=1:return False
 s=snaps[0];w=s.get('words',[])
 tuples=[x for x in events if x.get('event')=='startup_csr' and x.get('phase')=='after_library_before_Open']
 return (snapshot_valid(s) and s.get('phase')=='after_library_before_Open' and s.get('sequence')==2 and
  bool(tuples) and tuples[-1]['status']==0 and tuples[-1]['request']==tuples[-1]['response']==2 and
  any(x.get('event')=='SDK_loaded_no_Open_no_CSR_yet' for x in events) and
  all(w[8+16*c]==w[9+16*c]==w[11+16*c]==0 for c in range(6)) and
  w[79]==w[77]==w[95]==w[93]==w[1])
def software(n):
 r=runtime(n);assets=cfg['software_assets']
 for row in assets.values():b.verify_file(Path(row['path']),row)
 out,result=run_child('software',lambda out:[assets['startup_init_supervisor']['path'],str(out/'trace.jsonl'),assets['startup_sdk_child']['path'],'--library-first'])
 rows=[json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines()] if (out/'trace.jsonl').exists() else []
 snaps=[x for x in rows if x.get('event')=='startup_snapshot']
 result.update(passed=False,snapshots=snaps,events=[x for x in rows if 'words' not in x],SDK_Open_attempts=sum(x.get('event')=='before_Device_Open' for x in rows))
 same=result['boot_id']==r['boot_id'] and not result['device_owners']
 if result['exit_code']==0:
  result['passed']=(same and [(s['phase'],s['sequence']) for s in snaps]==[('after_library_before_Open',2),('Device_Open',4),('idle_after_Open',6),('Device_Close_and_unload',8)] and
   all(snapshot_valid(s) for s in snaps) and idle_healthy(snaps[0]) and idle_healthy(snaps[2]) and
   all(s['words'][95]==0 for s in snaps) and result['SDK_Open_attempts']==1 and any(x.get('event')=='SOFTWARE_INIT_OBSERVATION_COMPLETE' for x in rows))
 result['recognized_preopen_fault']=same and recognized_preopen_fault(result)
 b.save_new(b.META/'software.json',result);return result
def post_reset(n):
 r=runtime(n);attempt=read('physical-reset-attempt');human=read('user-reset')
 b.need(attempt['cycle']==n and attempt['boot_id']==r['boot_id'] and record(n,'software')['recognized_preopen_fault'],'No eligible fault/reset request')
 b.need(human.get('confirmed_by')=='user' and human.get('key')=='PL_KEY1/SW6' and human.get('pulses')==1 and human.get('boot_id')==r['boot_id'],'Actual correct-key release not confirmed')
 b.verify_file(PACKAGE/'ai_preopen_monitor',cfg['files']['ai_preopen_monitor'])
 out,result=run_child('post-reset',lambda out:[str(PACKAGE/'ai_preopen_monitor'),str(out/'trace.jsonl')])
 initial=[]
 for line in (out/'stderr.log').read_text(errors='replace').splitlines():
  if line.startswith('PREOPEN_CSR_INITIAL '):initial.append(json.loads(line[len('PREOPEN_CSR_INITIAL '):]))
 result.update(initial_values=initial[-1] if initial else None,valid=False,healthy=False,SDK_load=False)
 if result['exit_code']==0:
  s=json.loads((out/'trace.jsonl').read_text());result['snapshot']=s
  result['valid']=snapshot_valid(s) and s['status']==0 and s['request']==s['response']==2 and result['boot_id']==r['boot_id'] and not result['device_owners']
  result['healthy']=result['valid'] and idle_healthy(s)
 b.save_new(b.META/'post-reset.json',result);return result
def main(stage,n):
 b.need(HERE==BASE and str(BASE)=='/root/hdmi-library-reset-20261019-r22','Wrong r22 location')
 if stage=='audit':return b.audit(ORIGINAL)
 a=authorize();bind(n)
 if stage=='prepare':
  b.need(n==1,'Prepare once');audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id']);b.checked_backup()
  for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
  for row in cfg['software_assets'].values():b.verify_file(Path(row['path']),row)
  host=cfg['independent_host_backup'];b.need(host['verified'] and host['sha256']==ORIGINAL and host['bytes']==7023552,'Host original backup absent')
  return save('prepare',dict(passed=True,boot_id=audit['boot_id'],reused_assets=True))
 if stage=='install':
  expected=prior(n);b.audit(ORIGINAL,expected);b.checked_backup();read('prepare')
  b.ROOT.mkdir(mode=0o700);b.META.mkdir(mode=0o700);b.MOUNT.mkdir(mode=0o700)
  return b.replace_boot(PACKAGE/'BOOT-ai-read-v3.bin',ORIGINAL,CANDIDATE,'install','install.json')
 if stage in ('candidate-reboot','fallback-reboot'):
  candidate=stage=='candidate-reboot';r=record(n,'install') if candidate else runtime(n)
  b.need(r['passed'] and r['boot_id']==b.boot_id(),'Boot install/runtime not verified')
  b.audit(CANDIDATE if candidate else ORIGINAL,r['boot_id'])
  name='candidate-'+str(n) if candidate else 'original-fallback'
  save(name+'-attempt',dict(boot_id=b.boot_id(),automatic_retry=False,time_unix=time.time()))
  p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  return dict(command_issued=True,helper_pid=p.pid,boot_id=b.boot_id())
 if stage=='restore':
  b.need(read('candidate-'+str(n)+'-attempt')['boot_id']!=b.boot_id(),'No new candidate boot');b.audit(CANDIDATE)
  return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
 if stage=='software':return software(n)
 if stage=='request-reset':
  r=runtime(n);b.need(record(n,'software')['recognized_preopen_fault'],'Not the recognized idle pre-Open fault')
  return save('physical-reset-attempt',dict(cycle=n,boot_id=r['boot_id'],key='PL_KEY1/SW6',pin='F8',pulses_max=1,SDK_Open=0))
 if stage=='post-reset':return post_reset(n)
 if stage=='close':
  b.need(record(n,'restore')['boot_id']!=b.boot_id(),'Candidate runtime still active');read('original-fallback-attempt')
  audit=b.audit(ORIGINAL);save('final-audit',audit)
  a.update(active=False,remaining_candidate_starts=0,remaining_original_fallbacks=0,remaining_key_pulses=0,remaining_SDK_Open=0)
  (BASE/'authorization.json').write_text(json.dumps(a,indent=2));return dict(closed=True,boot_id=audit['boot_id'])
 raise RuntimeError('Unknown stage')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','prepare','install','candidate-reboot','restore','software','request-reset','post-reset','fallback-reboot','close']);p.add_argument('--cycle',type=int,default=1);args=p.parse_args()
 try:print(json.dumps(main(args.stage,args.cycle),ensure_ascii=False,indent=2),flush=True)
 except BaseException:traceback.print_exc();raise SystemExit(1)
