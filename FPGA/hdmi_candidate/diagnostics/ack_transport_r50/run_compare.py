"""Synthetic ordinary network only; no SDK, MMIO, BOOT or reboot."""
from pathlib import Path
import importlib.util, json, os, shlex, subprocess, sys, time

w=Path(__file__).resolve().parent;o=Path('D:/FPGACompetitionProject')
e=o/'tools/pose-v1/evidence/hdmi-ack-transport-20261024-r50'
spec=importlib.util.spec_from_file_location('transport',w/'native_transport.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
if not any(x.split()[:3]==['192.168.126.49','ssh-ed25519',t.KEY] for x in t.KNOWN.read_text().splitlines()):
    raise RuntimeError('Pinned board identity differs')
env=os.environ.copy();env.update(SSH_ASKPASS=str(w/'NativeAskpass.exe'),SSH_ASKPASS_REQUIRE='force',DISPLAY='synthetic-ack-r50')
node='C:/Users/cenyongdong/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
base='/root/hdmi-ack-transport-20261024-r50'
summaries=[]
for name,exe,null in [('windows','C:/Windows/System32/OpenSSH/ssh.exe','NUL'),
                      ('git','C:/Program Files/Git/usr/bin/ssh.exe','/dev/null')]:
    host=tunnel=None
    output=e/(name+'-host')
    with (e/(name+'-host.stdout.log')).open('xb') as so,(e/(name+'-host.stderr.log')).open('xb') as se, (e/(name+'-forward.log')).open('xb') as sf:
        host=subprocess.Popen([node,str(w/'host.mjs'),str(output)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline=time.monotonic()+10
            while not (output/'ready.json').exists() and host.poll() is None and time.monotonic()<deadline:time.sleep(.05)
            if not (output/'ready.json').exists():raise RuntimeError('Synthetic host not ready')
            options=['-F',null,'-o','StrictHostKeyChecking=yes','-o','HostKeyAlgorithms=ssh-ed25519',
                     '-o','UserKnownHostsFile='+str(t.KNOWN),'-o','ConnectTimeout=5',
                     '-o','NumberOfPasswordPrompts=1','-o','PubkeyAuthentication=no',
                     '-o','PreferredAuthentications=password','-o','ExitOnForwardFailure=yes',
                     '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2']
            version=subprocess.run([exe,'-V'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10).stdout.decode(errors='replace').strip()
            tunnel=subprocess.Popen([exe,*options,'-N','-R','127.0.0.1:39481:127.0.0.1:39481',t.HOST],env=env,stdin=subprocess.DEVNULL,stdout=sf,stderr=sf,creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)
            if tunnel.poll() is not None:raise RuntimeError('Synthetic reverse forward failed')
            (e/(name+'-process.json')).write_text(json.dumps(dict(host=host.pid,tunnel=tunnel.pid,SSH=exe,version=version)))
            cmd='python3 '+shlex.quote(base+'/board_client.py')+' '+shlex.quote(base+'/'+name+'-client')
            subprocess.run([sys.executable,str(w/'board_call.py'),name+'-client','ssh',cmd,'--timeout','25'],check=True)
            code=host.wait(timeout=15)
            result=json.loads((output/'result.json').read_text())
            result.update(SSH=exe,version=version,host_exit=code)
            summaries.append(result)
            if code or not result['passed']:raise RuntimeError('Synthetic host exchange failed')
            print(json.dumps(dict(transport=name,**result)),flush=True)
        finally:
            if host is not None and host.poll() is None:host.terminate();host.wait(timeout=5)
            if tunnel is not None and tunnel.poll() is None:tunnel.terminate();tunnel.wait(timeout=5)
            (e/(name+'-closed.json')).write_text(json.dumps(dict(host_exit=None if host is None else host.returncode,tunnel_exit=None if tunnel is None else tunnel.returncode,closed=True)))
(e/'host-comparison.json').write_text(json.dumps(summaries,indent=2)+'\n')
