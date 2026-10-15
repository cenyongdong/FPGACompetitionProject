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

"""Read-only HDMI/clock/DT/driver inventory. No SDK, MMIO or ioctls."""
import os,json,hashlib,sys
from pathlib import Path

def read(p,limit=1048576):
    try:
        with Path(p).open('rb') as f:return f.read(limit).decode(errors='replace')
    except OSError:return None
out=None
base=Path('/sys/firmware/devicetree/base');nodes=[]
for directory,dirs,files in os.walk(str(base)):
    p=Path(directory);rel=str(p.relative_to(base));compat=read(p/'compatible') or ''
    if any(x in (rel+' '+compat).lower() for x in ('hdmi','display','video','vtc','v_tc','clock','udmabuf','amba_pl','reserved-memory','fpga')):
        props={}
        for name in ('compatible','status','reg','ranges','clocks','clock-names','clock-frequency','assigned-clock-rates','memory-region','size','dma-coherent','firmware-name'):
            if name in files:
                data=(p/name).read_bytes();props[name]={'hex':data.hex(),'text':data.replace(b'\0',b';').decode(errors='replace') if name in ('compatible','status','clock-names','firmware-name') else None}
        nodes.append({'path':rel,'properties':props})
drm=[]
for p in Path('/sys/class/drm').glob('*'):
    if not p.is_dir():continue
    data={'name':p.name,'status':read(p/'status'),'modes':read(p/'modes'),'enabled':read(p/'enabled'),'driver':os.path.realpath(str(p/'device/driver'))}
    edid=p/'edid'
    if edid.exists():
        try:
            b=edid.read_bytes();data.update(edid_bytes=len(b),edid_sha256=hashlib.sha256(b).hexdigest(),edid_hex=b.hex())
        except OSError as e:data['edid_error']=str(e)
    drm.append(data)
udma={}
for p in Path('/sys/class/u-dma-buf').glob('*'):
    udma[p.name]={n:read(p/n) for n in ('size','phys_addr','sync_mode','dma_coherent','dma_mask_bits')}
report={'scope':'read_only_no_MMIO_SDK_device_open_or_stream','display':'DELL E2421HN user connected','target':[1920,1080,60],
        'device_tree_model':read(base/'model'),'device_tree_compatible':read(base/'compatible'),'nodes':nodes,'drm':drm,
        'framebuffer':read('/proc/fb'),'framebuffer_devices':[str(p) for p in Path('/dev').glob('fb*')],
        'dri_devices':[str(p) for p in Path('/dev/dri').glob('*')],'udmabuf':udma,
        'clock_summary':read('/sys/kernel/debug/clk/clk_summary'),'iomem':read('/proc/iomem'),'interrupts':read('/proc/interrupts'),
        'kernel_cmdline':read('/proc/cmdline'),'fpga_state':read('/sys/class/fpga_manager/fpga0/state'),
        'fpga_firmware':read('/sys/class/fpga_manager/fpga0/firmware')}


report['recorded_at_utc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
report['scope']='read_only_no_MMIO_SDK_ioctl_mount_or_device_initialization; boot partition opened rb only'
report['identity']={'boot_files':fat_files(),'libraries':{n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in ('libicraft_hostbackend.so','libicraft_zg330backend.so','libicraft_xrt.so')},'packages':subprocess.check_output(['dpkg-query','-W','-f=${Package} ${Architecture} ${Version}\n','icraft:arm64','customop:arm64'],text=True,timeout=10).splitlines()}
report['uname']=list(os.uname())
report['processes']=subprocess.check_output(['ps','-eo','pid,comm'],text=True,timeout=10)
report['kernel_log_at_end_of_probe']=subprocess.check_output(['dmesg'],timeout=10).decode(errors='replace')
report['boot_id']=read('/proc/sys/kernel/random/boot_id')
report['mounts']=read('/proc/mounts')
report['i2c_adapter_names']={p.name:read(p/'name') for p in Path('/sys/class/i2c-adapter').glob('*')}
print(json.dumps(report,indent=2))
