"""Receive an authorized password before SSH starts; one-use local memory IPC.

No password in argv, environment, files, or logs. Existing known-host ED25519
key is mandatory. Uses the already bundled Git SSH/SCP; no package install.
"""
import argparse,getpass,ipaddress,os,subprocess,sys,threading,uuid
from pathlib import Path
from multiprocessing.connection import Listener,Client
ROOT=Path(__file__).resolve().parents[2]
GIT=Path('C:/Program Files/Git/usr/bin')
HOST='root@192.168.126.49'
KNOWN=Path('C:/Users/cenyongdong/.ssh/known_hosts')
KEY='AAAAC3NzaC1lZDI1NTE5AAAAIJEJjNFzYnjluPa+kwz4imgxJHRfVt462buoRP0JRtu6'
def main():
    if len(sys.argv)>1 and sys.argv[1]=='askpass':
        # Refuse unrelated host-key/passphrase dialogs; one password prompt only.
        assert any('password' in s.lower() for s in sys.argv[2:])
        with Client(os.environ['POSE_AUTH_CHANNEL'],family='AF_PIPE') as channel:
            sys.stdout.buffer.write(channel.recv_bytes()+b'\n');sys.stdout.buffer.flush()
        return
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['ssh','put','get']);p.add_argument('source');p.add_argument('destination',nargs='?');p.add_argument('--timeout',type=int,default=240);p.add_argument('--log',type=Path);p.add_argument('--reverse',action='store_true');p.add_argument('--stream',action='store_true');p.add_argument('--bind-address',type=ipaddress.ip_address);a=p.parse_args()
    assert 0<=a.timeout<=3600 and all((GIT/n).is_file() for n in ('ssh.exe','scp.exe')) and KNOWN.is_file()
    assert any(line.split()[:3]==['192.168.126.49','ssh-ed25519',KEY] for line in KNOWN.read_text().splitlines())
    cache=ROOT/'.local/pose-v1-ssh-transport';cache.mkdir(exist_ok=True);helper=cache/'askpass.sh'
    python=Path(sys.executable).as_posix();script=Path(__file__).as_posix()
    helper.write_text('#!/bin/sh\nexec "'+python+'" "'+script+'" askpass "$@"\n',encoding='utf-8',newline='\n')
    password=getpass.getpass('Authorized Lite password (memory only): ').encode()
    address=r'\\.\pipe\pose-auth-'+uuid.uuid4().hex
    listener=Listener(address,family='AF_PIPE')
    def serve():
        try:
            with listener.accept() as connection:connection.send_bytes(password)
        finally:listener.close()
    thread=threading.Thread(target=serve,daemon=True);thread.start()
    env=os.environ.copy();env.update(SSH_ASKPASS=helper.as_posix(),SSH_ASKPASS_REQUIRE='force',DISPLAY='pose-memory-auth',POSE_AUTH_CHANNEL=address)
    opts=['-F','/dev/null','-o','StrictHostKeyChecking=yes','-o','HostKeyAlgorithms=ssh-ed25519','-o','UserKnownHostsFile='+KNOWN.as_posix(),'-o','ConnectTimeout=5','-o','NumberOfPasswordPrompts=1','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password']
    if a.bind_address:opts.extend(['-o','BindAddress='+str(a.bind_address)])
    if a.reverse:opts.extend(['-o','ExitOnForwardFailure=yes','-R','127.0.0.1:39381:127.0.0.1:39381'])
    if a.mode=='ssh':args=[str(GIT/'ssh.exe'),*opts,'-T',HOST,a.source]
    else:
        assert a.destination
        remote=a.destination if a.mode=='put' else a.source
        assert remote.startswith('/root/demo-v1-20261022-r1/') and '..' not in Path(remote).parts
        local=Path(a.source if a.mode=='put' else a.destination)
        if a.mode=='get':assert not local.exists(),'Preserve prior return'
        args=[str(GIT/'scp.exe'),*opts,'-q',a.source,HOST+':'+a.destination] if a.mode=='put' else [str(GIT/'scp.exe'),*opts,'-q',HOST+':'+a.source,a.destination]
    try:
        if a.stream:
            if a.timeout!=0:raise ValueError('Streaming monitor requires --timeout 0; native load retains its own bound')
            log=a.log.open('xb') if a.log else None
            try:
                process=subprocess.Popen(args,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                for line in iter(process.stdout.readline,b''):
                    if log:log.write(line);log.flush()
                    sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
                sys.exit(process.wait())
            finally:
                if log:log.close()
        result=subprocess.run(args,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=(a.timeout or None))
        if a.log:
            assert not a.log.exists();a.log.write_bytes(result.stdout)
        sys.stdout.buffer.write(result.stdout);sys.stdout.buffer.flush();sys.exit(result.returncode)
    finally:
        if thread.is_alive():listener.close()
        password=b''
if __name__=='__main__':main()
