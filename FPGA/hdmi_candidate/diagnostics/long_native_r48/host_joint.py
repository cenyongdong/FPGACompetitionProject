from pathlib import Path
import os,subprocess,json,time,sys,importlib.util
O=Path('D:/FPGACompetitionProject');W=Path(__file__).resolve().parent
E=O/'tools/pose-v1/evidence/hdmi-long-native-20261024-r48'
spec=importlib.util.spec_from_file_location('transport',W/'native_transport.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
options=['-F','NUL','-o','StrictHostKeyChecking=yes','-o','HostKeyAlgorithms=ssh-ed25519','-o','UserKnownHostsFile='+str(t.KNOWN),'-o','ConnectTimeout=5','-o','NumberOfPasswordPrompts=1','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2']
assert any(l.split()[:3]==['192.168.126.49','ssh-ed25519',t.KEY] for l in t.KNOWN.read_text().splitlines())
env=os.environ.copy();env.update(SSH_ASKPASS=str(W/'NativeAskpass.exe'),SSH_ASKPASS_REQUIRE='force',DISPLAY='r36-joint')
with (E/'reverse-forward.log').open('xb') as tunnel_log,(E/'host.stdout.log').open('xb') as host_log,(E/'host.stderr.log').open('xb') as host_err:
 tunnel=subprocess.Popen(['C:/Windows/System32/OpenSSH/ssh.exe',*options,'-N','-R','127.0.0.1:39381:127.0.0.1:39381',t.HOST],env=env,stdin=subprocess.DEVNULL,stdout=tunnel_log,stderr=tunnel_log,creationflags=subprocess.CREATE_NO_WINDOW)
 (E/'forward-process.json').write_text(json.dumps(dict(pid=tunnel.pid,seconds_budget=2310)))
 host=None;start=time.monotonic()
 try:
  time.sleep(.5)
  if tunnel.poll() is not None:raise RuntimeError('Reverse forward failed; no SDK launch')
  host=subprocess.Popen(['node',str(O/'demo_v1/host/run.mjs'),'--stage','stress','--frames','52800','--data',str(O/'demo_v1/data/mixed'),'--output',str(E/'host'),'--linger','0','--pacer-python','C:/Users/cenyongdong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'],stdin=subprocess.DEVNULL,stdout=host_log,stderr=host_err,creationflags=subprocess.CREATE_NO_WINDOW)
  (E/'host-process.json').write_text(json.dumps(dict(pid=host.pid,frames=52800,input_hz=30)))
  while not (E/'host/runtime.json').exists() and host.poll() is None and time.monotonic()-start<15:time.sleep(.05)
  if not (E/'host/runtime.json').exists():raise RuntimeError('Host service not ready; no SDK launch')
  print('HOST_JOINT_READY '+(E/'host/runtime.json').read_text(),flush=True)
  while host.poll() is None:
   if tunnel.poll() is not None:raise RuntimeError('Reverse forward ended')
   if (E/'host-stop').exists() or time.monotonic()-start>2300:
    host.terminate();break
   try:host.wait(timeout=15)
   except subprocess.TimeoutExpired:print('HOST_JOINT_ACTIVE seconds=%.1f'%(time.monotonic()-start),flush=True)
  print('HOST_EXIT '+str(host.wait()),flush=True)
 finally:
  if host is not None and host.poll() is None:host.terminate();host.wait(timeout=10)
  if tunnel.poll() is None:tunnel.terminate();tunnel.wait(timeout=10)
  (E/'host-controller-closed.json').write_text(json.dumps(dict(host_exit=None if host is None else host.returncode,tunnel_exit=tunnel.returncode,seconds=time.monotonic()-start,closed=True)))
