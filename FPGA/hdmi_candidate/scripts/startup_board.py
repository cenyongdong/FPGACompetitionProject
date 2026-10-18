"""r14: at most three identical r9 startups, one Open each, no DMA/HDMI."""
from pathlib import Path
import argparse,json,os,subprocess,time,traceback
import board_support as b
HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text())
BASE=Path(cfg['base']);PACKAGE=BASE/'package';META=BASE/'metadata'
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-ai-read-v3.bin']['sha256']
b.CFG=cfg;b.PACKAGE=PACKAGE
b.identity_record=lambda x:dict(x,package_id=cfg['package_id'])
def load(path):return b.read_json(path)
def save(name,value):b.save_new(META/(name+'.json'),value);return value
def record(n,name):return load(BASE/('run-'+str(n))/'metadata'/(name+'.json'))
def bind(n):
 b.need(1<=n<=3,'Candidate sample outside approved cap')
 b.ROOT=BASE/('run-'+str(n));b.META=b.ROOT/'metadata';b.MOUNT=b.ROOT/'boot-mount'
def authorize():
 a=load(HERE/'authorization.json')
 b.need(a.get('active') is True and a.get('approved_by')=='user' and
        a.get('package_id')==cfg['package_id'] and a.get('candidate_starts_max')==3 and
        a.get('original_fallbacks_max')==1 and a.get('HDMI_long_term') is False,
        'Fresh r14 user approval absent; no action')
 return a
def restored(n):
 r=record(n,'restore');b.need(r['passed'] and r['BOOT_sha256']==ORIGINAL and r['boot_id']==b.boot_id(),'Original BOOT not restored in this runtime')
 return r
def prior(n):
 if n==1:return cfg['board']['pre_start_boot_id']
 r=restored(n-1);b.need(record(n-1,'probe')['passed'],'Previous startup abnormal; no next candidate')
 return r['boot_id']
def boot_command(kind,n):
 name='candidate-'+str(n) if kind=='candidate' else 'original-fallback'
 if kind=='candidate':
  r=record(n,'install');b.need(r['passed'] and r['boot_id']==b.boot_id(),'Candidate install not verified')
  audit=b.audit(CANDIDATE,r['boot_id'])
 else:
  r=restored(n);audit=b.audit(ORIGINAL,r['boot_id'])
 # Durable, exclusive reservation is the count. Lost SSH never permits resend.
 save(name+'-attempt',dict(boot_id=audit['boot_id'],time_unix=time.time(),automatic_retry=False))
 p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 return save(name+'-issued',dict(boot_id=audit['boot_id'],helper_pid=p.pid,command_issued=True))
def probe(n):
 r=restored(n);b.audit(ORIGINAL,r['boot_id'])
 exe=PACKAGE/'ai_startup_probe';b.verify_file(exe,cfg['files']['ai_startup_probe']);os.chmod(exe,0o700)
 b.reserve('probe',dict(SDK_Open_max=1,DMA=False,HDMI=False,automatic_retry=False))
 out=b.ROOT/'output';out.mkdir(mode=0o700);start=time.monotonic()
 with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
  p=subprocess.Popen([str(exe),str(out/'trace.jsonl'),'--allow-device-init'],cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
  b.save_new(b.META/'probe-process.json',dict(pid=p.pid,boot_id=b.boot_id(),time_unix=time.time(),soft_monitor_seconds=25))
  while p.poll() is None:
   try:p.wait(timeout=25)
   except subprocess.TimeoutExpired:
    print(json.dumps(dict(event='still_running',pid=p.pid,seconds=time.monotonic()-start,proc=b.proc_snapshot(p.pid))),flush=True)
 owners=b.owners();result=dict(exit_code=p.returncode,seconds=time.monotonic()-start,boot_id=b.boot_id(),device_owners=owners,passed=False)
 trace=out/'trace.jsonl';rows=[json.loads(x) for x in trace.read_text().splitlines()] if trace.exists() else []
 snaps=[x for x in rows if x.get('event')=='startup_snapshot']
 result['snapshots']=snaps
 if p.returncode==0:
  b.need(not owners and not Path('/proc/'+str(p.pid)).exists(),'Child/device owner remains')
  b.need([(x['phase'],x['sequence']) for x in snaps]==[('before_Open',2),('during_Open',4),('after_Open',6),('during_Close',8)],'Incomplete startup observation')
  b.need(all(len(x['words'])==104 and x['words'][0]==0x41495201 for x in snaps),'Invalid full raw snapshot')
  b.need(sum(x.get('event')=='before_Device_Open' for x in rows)==1,'Open count differs')
  for x in snaps:
   w=x['words'];b.need(w[8+16*4+7]==0 and all(w[8+16*c+3]==0 for c in range(6)),'HDMI RVALID/nonOKAY response')
   if x['phase'] in ('before_Open','after_Open'):
    b.need(w[1]>0 and (w[2]&31)==0x19 and w[3]==0 and all(w[8+16*c]==w[9+16*c]==0 for c in range(6)),'Idle/reset gate failed')
  result['passed']=True
 b.save_new(b.META/'probe.json',result)
 return result
def main(stage,n):
 b.need(BASE.is_absolute() and BASE==HERE and str(BASE)=='/root/hdmi-startup-20261018-r14','Unexpected packet location')
 if stage=='audit':return b.audit(ORIGINAL)
 a=authorize();bind(n)
 if stage=='prepare':
  b.need(n==1,'Prepare once only')
  for path in (BASE,PACKAGE,META,b.ROOT,b.META):b.need(path.is_dir() and not path.is_symlink(),'Missing/unsafe package directory')
  for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
  result=b.prepare();return save('prepare',result)
 if stage=='install':
  expected=prior(n);b.audit(ORIGINAL,expected);b.checked_backup()
  host=load(META/'host-backup.json');b.need(host['passed'] and host['sha256']==ORIGINAL and host['bytes']==7023552,'Independent host backup absent')
  load(META/'prepare.json')
  if n>1:
   b.ROOT.mkdir(mode=0o700);b.META.mkdir(mode=0o700);b.MOUNT.mkdir(mode=0o700)
  return b.replace_boot(PACKAGE/'BOOT-ai-read-v3.bin',ORIGINAL,CANDIDATE,'install','install.json')
 if stage=='candidate-reboot':return boot_command('candidate',n)
 if stage=='restore':
  previous=load(META/('candidate-'+str(n)+'-attempt.json'))['boot_id']
  b.need(previous!=b.boot_id(),'Candidate startup did not change boot_id')
  b.audit(CANDIDATE);b.checked_backup()
  return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
 if stage=='probe':return probe(n)
 if stage=='fallback-reboot':return boot_command('original',n)
 if stage=='close':
  r=record(n,'restore');b.need(r['boot_id']!=b.boot_id(),'Candidate runtime still active')
  load(META/'original-fallback-attempt.json');final=b.audit(ORIGINAL)
  save('final-audit',final);a['active']=False;a['remaining_candidate_starts']=0;a['remaining_original_fallbacks']=0
  with (HERE/'authorization.json').open('w') as f:json.dump(a,f,indent=2);f.flush();os.fsync(f.fileno())
  return dict(closed=True,boot_id=final['boot_id'])
 raise RuntimeError('Unknown stage')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','install','candidate-reboot','restore','probe','fallback-reboot','audit','close']);parser.add_argument('--cycle',type=int,default=1);args=parser.parse_args()
 try:print(json.dumps(main(args.stage,args.cycle),ensure_ascii=False,indent=2),flush=True)
 except BaseException:
  traceback.print_exc();raise SystemExit(1)
