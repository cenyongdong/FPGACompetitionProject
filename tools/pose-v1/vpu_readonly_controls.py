"""Idle-context QUERYCTRL/G_CTRL only; no S_CTRL/S_FMT/stream or MMIO."""
import fcntl,os,struct,json,sys
from pathlib import Path

out=Path(sys.argv[1]);assert not out.exists()
# Linux generic AArch64 ioctl ABI; queryctrl68B/control8B, no pointer fields.
Q=(3<<30)|(68<<16)|(ord('V')<<8)|36
G=(3<<30)|(8<<16)|(ord('V')<<8)|27
fd=os.open('/dev/video0',os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
records=[];previous=0
try:
    for _ in range(256):
        b=bytearray(68);struct.pack_into('I',b,0,previous|0x80000000)
        try:fcntl.ioctl(fd,Q,b,True)
        except OSError as e:
            terminal_errno=e.errno;break
        ctrl_id,kind=struct.unpack_from('II',b)
        assert ctrl_id>previous
        name=bytes(b[8:40]).split(b'\0')[0].decode(errors='replace')
        minimum,maximum,step,default,flags=struct.unpack_from('iiiiI',b,40)
        row={'id':ctrl_id,'name':name,'type':kind,'min':minimum,'max':maximum,'step':step,'default':default,'flags':flags}
        value=bytearray(struct.pack('Ii',ctrl_id,0))
        try:fcntl.ioctl(fd,G,value,True);row['idle_value']=struct.unpack_from('i',value,4)[0]
        except OSError as e:row['get_errno']=e.errno
        records.append(row);previous=ctrl_id
    else:raise RuntimeError('Control count unbounded')
finally:os.close(fd)
report={'scope':'idle_context_defaults_readonly_not_values_of_closed_r2_session','QUERYCTRL_bytes':68,'QUERYCTRL_ioctl':Q,'G_CTRL_bytes':8,'G_CTRL_ioctl':G,
        'terminal_errno':terminal_errno,'controls':records,'S_CTRL_or_stream_executed':False}
out.write_bytes((json.dumps(report,indent=2)+'\n').encode());print('Read-only controls',len(records))
