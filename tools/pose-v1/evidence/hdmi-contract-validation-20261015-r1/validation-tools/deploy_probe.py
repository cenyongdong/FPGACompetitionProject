"""Finite identity-gated deployment and one display-register read invocation."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3'
S=R/'.local/hdmi-register-probe-20261015-r3'
T=S/'secure_transport.py'
REMOTE='/tmp/hdmi-register-probe-20261015-r3'
steps=[]
def call(name,mode,source,destination=None,timeout=30):
    args=[sys.executable,str(T),mode,source]
    if destination:args.append(destination)
    args+=['--timeout',str(timeout),'--log',str(E/(name+'.remote.txt'))]
    t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=timeout+10)
    (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
    steps.append({'stage':name,'mode':mode,'exit':p.returncode,'seconds':time.monotonic()-t,'timeout_seconds':timeout})
    (E/'transport-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8')
    if p.returncode:raise RuntimeError(name+' failed; evidence preserved; no repeat invocation')

def main():
    assert not (E/'transport-steps.json').exists()
    build=json.loads((E/'build-result.json').read_text())
    assert build['compiled'] and hashlib.sha256((E/'hdmi_readonly_probe').read_bytes()).hexdigest()==build['binary_sha256']
    prior=(R/'.local/shared-stability-transport-20261015-r2/secure_transport.py').read_text(encoding='utf-8')
    T.write_text(prior.replace('/tmp/wifi-pose-shared-stability-20261015-r2/',REMOTE+'/'),encoding='utf-8',newline='\n')
    preflight=(R/'tools/pose-v1/board_application_preflight.py').read_text(encoding='utf-8')
    functions=preflight[:preflight.index('out=pathlib.Path(sys.argv[1])')]
    expected={'libraries':build['libraries'],'binary_sha256':build['binary_sha256'],
        'BOOT_sha256':'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'}
    (E/'expected.json').write_text(json.dumps(expected,indent=2)+'\n',encoding='utf-8')
    # This preflight does not initialize the SDK or start the binary.
    check=functions+"\nexpected="+repr(expected)+"\n"+'''
boot=next(x for x in fat_files() if x['name']=='BOOT.BIN')
assert boot['sha256']==expected['BOOT_sha256'],'BOOT changed; stop'
actual={n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']}
assert actual==expected['libraries'],'SDK changed; stop'
print(json.dumps({'boot':boot,'libraries':actual,'fpga_state':pathlib.Path('/sys/class/fpga_manager/fpga0/state').read_text()}))
'''
    (E/'preflight-code.py').write_text(check,encoding='utf-8')
    call('01-identity','ssh','python3 -c '+shlex.quote(check))
    call('02-fresh-directory','ssh','mkdir -- '+REMOTE)
    call('03-transfer','put',str(E/'hdmi_readonly_probe'),REMOTE+'/hdmi_readonly_probe')
    driver=functions+'\nexpected='+repr(expected)+'\nremote='+repr(REMOTE)+'\n'+'''
import os,signal,time
binary=pathlib.Path(remote)/'hdmi_readonly_probe'
assert digest(binary)==expected['binary_sha256'],'Transferred binary differs; stop'
assert next(x for x in fat_files() if x['name']=='BOOT.BIN')['sha256']==expected['BOOT_sha256']
assert {n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']}==expected['libraries']
binary.chmod(0o700)
before=subprocess.check_output(['dmesg'])
started=time.monotonic()
p=subprocess.Popen([str(binary)],cwd=remote,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
timed_out=False
try:stdout,stderr=p.communicate(timeout=10)
except subprocess.TimeoutExpired:
 timed_out=True
 os.killpg(p.pid,signal.SIGKILL)
 stdout,stderr=p.communicate(timeout=5)
after=subprocess.check_output(['dmesg'])
result={'probe_exit':p.returncode,'timeout':timed_out,'budget_seconds':10,'elapsed_seconds':time.monotonic()-started,
 'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace'),
 'dmesg_before':before.decode(errors='replace'),'dmesg_after':after.decode(errors='replace'),
 'kernel_log_unchanged':before==after,'child_reaped':p.poll() is not None,
 'boot_after':next(x for x in fat_files() if x['name']=='BOOT.BIN'),
 'libraries_after':{n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']},
 'fpga_state':pathlib.Path('/sys/class/fpga_manager/fpga0/state').read_text(),
 'scope':'SDK lifecycle + version + 12 whitelisted reads, no explicit application register writes, Session, model, allocation, reset or DMA start'}
print(json.dumps(result,indent=2))
assert not timed_out and p.returncode==0,'Probe failed; do not retry'
assert before==after,'Kernel log changed; stop'
assert result['boot_after']['sha256']==expected['BOOT_sha256'] and result['libraries_after']==expected['libraries'],'Identity changed; stop'
'''
    (E/'board-driver.py').write_text(driver,encoding='utf-8',newline='\n')
    call('04-run-once','ssh','python3 -c '+shlex.quote(driver),timeout=30)
    result=json.loads((E/'04-run-once.remote.txt').read_text(encoding='utf-8'))
    print(result['stdout'])
    print('Probe exit',result['probe_exit'],'kernel unchanged',result['kernel_log_unchanged'],'seconds',result['elapsed_seconds'])
    (E/'review.json').write_text(json.dumps({'probe_passed':result['probe_exit']==0,'kernel_unchanged':result['kernel_log_unchanged'],
        'no_scanout_started':True,'BOOT_SDK_unchanged':True,'child_reaped':result['child_reaped'],'pixel_clock_measured':False,
        'scope':'Register fingerprint only, not source-to-bitstream proof or HDMI acceptance'},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
