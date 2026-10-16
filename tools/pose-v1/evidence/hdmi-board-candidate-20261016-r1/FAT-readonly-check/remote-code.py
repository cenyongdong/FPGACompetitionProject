import pathlib,struct,subprocess,shutil,json
assert not any(v.split()[0]=='/dev/mmcblk0p1' for v in pathlib.Path('/proc/mounts').read_text().splitlines())
with open('/dev/mmcblk0p1','rb') as f:
 b=f.read(512);bps=struct.unpack_from('<H',b,11)[0];reserved=struct.unpack_from('<H',b,14)[0];nf=b[16];spf=struct.unpack_from('<H',b,22)[0];assert bps==512 and nf==2 and spf>0
 tables=[]
 for i in range(nf):f.seek((reserved+i*spf)*bps);tables.append(f.read(spf*bps))
 entry1=struct.unpack_from('<H',tables[0],2)[0]
checker=shutil.which('fsck.fat') or shutil.which('fsck.vfat') or shutil.which('dosfsck')
result={'FAT_tables_identical':tables[0]==tables[1],'FAT16_entry1_hex':hex(entry1),'clean_shutdown_bit':bool(entry1&0x8000),'no_hard_error_bit':bool(entry1&0x4000),'BPB_state_byte_37':b[37],'checker':checker,'repair_performed':False}
if checker:
 p=subprocess.run([checker,'-n','-v','/dev/mmcblk0p1'],capture_output=True,timeout=30);result.update(checker_exit=p.returncode,checker_stdout=p.stdout.decode(errors='replace'),checker_stderr=p.stderr.decode(errors='replace'))
print(json.dumps(result,indent=2))
