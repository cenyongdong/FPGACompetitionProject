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

expected={'libraries': {'libicraft_hostbackend.so': 'd0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130', 'libicraft_zg330backend.so': '592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57', 'libicraft_xrt.so': 'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96', 'libicraft_xir.so': '377a2cac1a8834836503d9805451449d42d99a888b8f96b38d4c2ba8c585af3e', 'libicraft_utils.so': '99679371aa20e7955e14c39938225df24cdc763d75f26301970fba114f650109', 'libaxizg330aiu.so': 'd55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178'}, 'binary_sha256': '7dcc8c4e383ee7aad7021bf002c838a0ff652a18ad4053b747422e8d0fde4fb6', 'BOOT_sha256': '22035d99f2dacdcb1817a0c08ae8b04c3b024e51bf2f1b522f0fcb9baf252135'}

import os, glob
def read(p):
 try:return pathlib.Path(p).read_text().strip()
 except (OSError,UnicodeError):return None
boot=next(x for x in fat_files() if x['name']=='BOOT.BIN')
libs={n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']}
assert boot['sha256']==expected['BOOT_sha256'],'BOOT identity changed; stop'
assert libs==expected['libraries'],'SDK identity changed; stop'
processes=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 item={'pid':int(p.name),'comm':read(p/'comm'),'device_fds':[]}
 try:files=list((p/'fd').iterdir())
 except OSError:continue
 for f in files:
  try:target=os.readlink(f)
  except OSError:continue
  if target.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri','/dev/xdma')):item['device_fds'].append({'fd':f.name,'target':target})
 processes.append(item)
sysfs={}
for root in ['/sys/class/fpga_manager','/sys/class/fpga_bridge','/sys/class/fpga_region']:
 sysfs[root]=[]
 for p in pathlib.Path(root).glob('*'):
  sysfs[root].append({'name':p.name,'path':str(p.resolve()),'attrs':{n:read(p/n) for n in ['name','state','status','flags','firmware','enable']},'entries':[x.name for x in p.iterdir()]})
dt=[]
for p in pathlib.Path('/sys/firmware/devicetree/base').rglob('compatible'):
 b=p.read_bytes()
 if any(k in b.lower() for k in [b'fpga',b'devcfg',b'decouple',b'bridge',b'zynq']):
  dt.append({'path':str(p.parent),'compatible':b.decode(errors='replace').split(chr(0)),'status':read(p.parent/'status')})
kernel=subprocess.check_output(['dmesg']).decode(errors='replace')
result={'scope':'Read-only boot block hashes, libraries, proc/sysfs/device-tree; no MMIO/SDK/configuration writes',
 'BOOT':boot,'libraries':libs,'boot_id':read('/proc/sys/kernel/random/boot_id'),
 'uname':subprocess.check_output(['uname','-a']).decode().strip(),
 'fpga_state':read('/sys/class/fpga_manager/fpga0/state'),'processes':processes,
 'device_owners':[p for p in processes if p['device_fds']], 'fpga_sysfs':sysfs,'device_tree':dt,
 'kernel_log':kernel,'kernel_sha256':hashlib.sha256(kernel.encode()).hexdigest(),
 'memory':read('/proc/meminfo'),'mounts':read('/proc/mounts'),
 'devcfg_devices':glob.glob('/dev/*devcfg*'),'note':'No FD owner does not prove AXI drain.'}
print(json.dumps(result,indent=2))
