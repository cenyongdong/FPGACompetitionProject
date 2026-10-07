"""Read sysfs/devicetree/proc only; never mount, SDK-open or touch MMIO."""
import json,pathlib,sys,os
out=pathlib.Path(sys.argv[1]);assert not out.exists(),'Preserve video audit'
def read(p,limit=262144):
    p=pathlib.Path(p)
    try:
        with p.open('rb') as f:return f.read(limit).decode('utf-8',errors='replace')
    except (OSError,ValueError):return None
base=pathlib.Path('/sys/firmware/devicetree/base');nodes=[]
for directory,subdirs,files in os.walk(str(base)):
    rel=str(pathlib.Path(directory).relative_to(base));p=pathlib.Path(directory)
    compatible=(p/'compatible').read_bytes().replace(b'\0',b';').decode(errors='replace') if 'compatible' in files else ''
    if any(s in (rel+' '+compatible).lower() for s in ['video','hdmi','display','vpu','mvx','mve','udmabuf','mali-v','amba_pl','clock']):
        props={}
        for name in ['compatible','status','reg','clocks','clock-names','clock-frequency','assigned-clock-rates','memory-region','size','dma-coherent','ranges']:
            if name in files:
                raw=(p/name).read_bytes();props[name]=dict(hex=raw.hex(),text=raw.replace(b'\0',b';').decode(errors='replace') if name in ['compatible','status','clock-names'] else None)
        nodes.append(dict(path=rel,properties=props))
video=[]
for p in pathlib.Path('/sys/class/video4linux').glob('video*'):
    video.append(dict(node='/dev/'+p.name,name=read(p/'name'),driver=os.path.realpath(str(p/'device/driver')),dev=read(p/'dev')))
report=dict(scope='sysfs_proc_only_no_device_configuration',device_tree_nodes=nodes,video_nodes=video,fpga_state=read('/sys/class/fpga_manager/fpga0/state'),
            framebuffer=read('/proc/fb'),clock_summary=read('/sys/kernel/debug/clk/clk_summary'),udmabuf_size=read('/sys/class/u-dma-buf/udmabuf0/size'),
            cmdline=read('/proc/cmdline'),display_connected_user_report=False)
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Read-only video audit saved',out)
