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
            if name!='UENV.TXT':continue
            assert struct.unpack_from('<I',e,28)[0]<=65536,'uEnv unexpectedly large'
            chunks=[]
            remaining=struct.unpack_from('<I',e,28)[0];cluster=struct.unpack_from('<H',e,26)[0];seen=set();h=hashlib.sha256()
            while remaining:
                assert 2<=cluster<0xfff0 and cluster not in seen and cluster*2+2<=len(fat),'Invalid FAT chain'
                seen.add(cluster);f.seek((data_sector+(cluster-2)*spc)*bps);block=f.read(min(remaining,spc*bps));assert block,'Truncated FAT content';h.update(block);chunks.append(block);remaining-=len(block);cluster=struct.unpack_from('<H',fat,cluster*2)[0]
            result.append(dict(name=name,size=struct.unpack_from('<I',e,28)[0],sha256=h.hexdigest(),text=b''.join(chunks).decode('utf-8')))
        return result


files=fat_files()
assert len(files)==1,'uEnv missing or duplicated'
print(json.dumps({'uEnv':files[0],'cmdline':pathlib.Path('/proc/cmdline').read_text(),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'scope':'Read-only FAT root/uEnv and proc; no mount/SDK/MMIO/configuration writes'},indent=2))
