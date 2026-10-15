"""Read-only Lite SDK/BOOT identity audit. No mount, device init or register access."""
import hashlib,json,pathlib,struct,subprocess,sys
def digest(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        while True:
            b=f.read(1048576)
            if not b:break
            h.update(b)
    return h.hexdigest()
def fat_files():
    with open('/dev/mmcblk0p1','rb') as f:
        boot=f.read(512);bps=struct.unpack_from('<H',boot,11)[0];spc=boot[13];reserved=struct.unpack_from('<H',boot,14)[0];nf=boot[16];entries=struct.unpack_from('<H',boot,17)[0];spf=struct.unpack_from('<H',boot,22)[0]
        assert bps==512 and spc>0 and nf in (1,2) and spf>0 and entries>0 and boot[510:512]==b'\x55\xaa','Unexpected FAT16 BPB'
        root_sector=reserved+nf*spf;root_len=(entries*32+bps-1)//bps;data_sector=root_sector+root_len
        f.seek(reserved*bps);fat=f.read(spf*bps);f.seek(root_sector*bps);root=f.read(entries*32);result=[]
        for i in range(0,len(root),32):
            e=root[i:i+32]
            if e[0]==0:break
            if e[0]==229 or e[11]&0x18 or e[11]==15:continue
            name=e[:8].decode('ascii').rstrip();ext=e[8:11].decode('ascii').rstrip();name+=('.'+ext) if ext else ''
            remaining=struct.unpack_from('<I',e,28)[0];cluster=struct.unpack_from('<H',e,26)[0];seen=set();h=hashlib.sha256()
            while remaining:
                assert 2<=cluster<0xfff0 and cluster not in seen and cluster*2+2<=len(fat),'Invalid FAT chain'
                seen.add(cluster);f.seek((data_sector+(cluster-2)*spc)*bps);block=f.read(min(remaining,spc*bps));assert block,'Truncated FAT content';h.update(block);remaining-=len(block);cluster=struct.unpack_from('<H',fat,cluster*2)[0]
            result.append(dict(name=name,size=struct.unpack_from('<I',e,28)[0],sha256=h.hexdigest()))
        return result

expected={'libraries': {'libicraft_hostbackend.so': 'd0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130', 'libicraft_zg330backend.so': '592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57', 'libicraft_xrt.so': 'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96', 'libicraft_xir.so': '377a2cac1a8834836503d9805451449d42d99a888b8f96b38d4c2ba8c585af3e', 'libicraft_utils.so': '99679371aa20e7955e14c39938225df24cdc763d75f26301970fba114f650109', 'libaxizg330aiu.so': 'd55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178'}, 'binary_sha256': '7dcc8c4e383ee7aad7021bf002c838a0ff652a18ad4053b747422e8d0fde4fb6', 'BOOT_sha256': 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'}
remote='/tmp/hdmi-register-probe-20261015-r3'

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
