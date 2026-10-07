"""Read-only HDMI/clock/DT/driver inventory. No SDK, MMIO or ioctls."""
import os,json,hashlib,sys
from pathlib import Path

def read(p,limit=1048576):
    try:
        with Path(p).open('rb') as f:return f.read(limit).decode(errors='replace')
    except OSError:return None
out=Path(sys.argv[1]);assert not out.exists()
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
out.write_bytes((json.dumps(report,indent=2)+'\n').encode());print('Read-only HDMI inventory saved')
