import os,pathlib,json,struct,shutil
assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='8974fbf7-cbe9-4fc9-954d-4682c45b045f'
with open('/dev/mmcblk0p1','rb') as f:
 b=f.read(512);bps=struct.unpack_from('<H',b,11)[0];spc=b[13];reserved=struct.unpack_from('<H',b,14)[0];nf=b[16];entries=struct.unpack_from('<H',b,17)[0];spf=struct.unpack_from('<H',b,22)[0];total=struct.unpack_from('<H',b,19)[0] or struct.unpack_from('<I',b,32)[0]
 assert bps==512 and spc>0 and nf in (1,2) and entries>0 and spf>0 and b[510:512]==b'\x55\xaa'
 clusters=(total-reserved-nf*spf-(entries*32+bps-1)//bps)//spc;assert 4085<=clusters<65525
 f.seek(reserved*bps);fat=f.read(spf*bps);assert (clusters+2)*2<=len(fat)
 free=sum(struct.unpack_from('<H',fat,i*2)[0]==0 for i in range(2,clusters+2))*spc*bps
out={'boot_partition':'/dev/mmcblk0p1','filesystem':'FAT16','currently_mounted':any(l.split()[0]=='/dev/mmcblk0p1' for l in pathlib.Path('/proc/mounts').read_text().splitlines()),'free_FAT_bytes':free,'root_disk_usage':shutil.disk_usage('/')._asdict(),'tools':{n:shutil.which(n) for n in ['mount','umount','sync','reboot','sha256sum','cp','mv']},'changed_or_mounted':False}
print(json.dumps(out,indent=2))
