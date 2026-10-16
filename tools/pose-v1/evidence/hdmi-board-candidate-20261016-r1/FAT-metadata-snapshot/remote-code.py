import pathlib,struct,json,base64
assert not any(v.split()[0]=='/dev/mmcblk0p1' for v in pathlib.Path('/proc/mounts').read_text().splitlines())
with open('/dev/mmcblk0p1','rb') as f:
 b=f.read(512);bps=struct.unpack_from('<H',b,11)[0];reserved=struct.unpack_from('<H',b,14)[0];nf=b[16];spf=struct.unpack_from('<H',b,22)[0];entries=struct.unpack_from('<H',b,17)[0];assert bps==512 and nf==2 and 0<spf<512 and entries<=4096
 f.seek(reserved*bps);fat=f.read(spf*bps);fat2=f.read(spf*bps);f.seek((reserved+nf*spf)*bps);root=f.read(entries*32)
 print(json.dumps({'boot_sector':base64.b64encode(b).decode(),'FAT1':base64.b64encode(fat).decode(),'FAT2':base64.b64encode(fat2).decode(),'root_directory':base64.b64encode(root).decode(),'read_only':True}))
