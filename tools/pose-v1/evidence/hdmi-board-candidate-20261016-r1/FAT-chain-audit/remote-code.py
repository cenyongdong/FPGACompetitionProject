import pathlib,struct,json
assert not any(v.split()[0]=='/dev/mmcblk0p1' for v in pathlib.Path('/proc/mounts').read_text().splitlines())
errors=[];owners={};file_count=0;directory_count=0;file_bytes=0;entries_seen=0
with open('/dev/mmcblk0p1','rb') as f:
 b=f.read(512);bps=struct.unpack_from('<H',b,11)[0];spc=b[13];reserved=struct.unpack_from('<H',b,14)[0];nf=b[16];entries=struct.unpack_from('<H',b,17)[0];spf=struct.unpack_from('<H',b,22)[0];total=struct.unpack_from('<H',b,19)[0] or struct.unpack_from('<I',b,32)[0]
 assert bps==512 and spc>0 and nf==2 and entries>0 and spf>0
 root_sector=reserved+nf*spf;root_sectors=(entries*32+bps-1)//bps;data_sector=root_sector+root_sectors;count=(total-data_sector)//spc;assert 4085<=count<65525
 f.seek(reserved*bps);fat=f.read(spf*bps);fat2=f.read(spf*bps);assert fat==fat2
 def chain(start,name):
  current=start;seen=[]
  while current<0xfff8:
   assert 2<=current<count+2 and current not in seen,'invalid or looping chain '+name
   assert current not in owners,'crosslinked chain '+name+' '+owners.get(current,'')
   owners[current]=name;seen.append(current);current=struct.unpack_from('<H',fat,current*2)[0]
  return seen
 def directory(data,prefix,depth):
  global file_count,directory_count,file_bytes,entries_seen
  assert depth<=16 and len(data)<=2097152
  for i in range(0,len(data),32):
   q=data[i:i+32];assert len(q)==32
   if q[0]==0:break
   if q[0]==229 or q[11]==15 or q[11]&8:continue
   name=q[:8].decode('ascii',errors='replace').rstrip();ext=q[8:11].decode('ascii',errors='replace').rstrip();name+=('.'+ext) if ext else ''
   if name in ('.','..'):continue
   entries_seen+=1;assert entries_seen<=4096
   name=prefix+'/'+name;start=struct.unpack_from('<H',q,26)[0];size=struct.unpack_from('<I',q,28)[0]
   blocks=chain(start,name) if start else []
   if q[11]&16:
    directory_count+=1;buf=[]
    for n in blocks:f.seek((data_sector+(n-2)*spc)*bps);buf.append(f.read(spc*bps))
    directory(b''.join(buf),name,depth+1)
   else:
    file_count+=1;file_bytes+=size;assert len(blocks)==(size+spc*bps-1)//(spc*bps),'file chain length mismatch '+name
 f.seek(root_sector*bps);directory(f.read(entries*32),'',0)
 allocated={i for i in range(2,count+2) if struct.unpack_from('<H',fat,i*2)[0]!=0}
 lost=allocated-set(owners)
 print(json.dumps({'FAT_tables_identical':True,'files':file_count,'directories':directory_count,'file_bytes':file_bytes,'owned_clusters':len(owners),'allocated_clusters':len(allocated),'lost_cluster_count':len(lost),'lost_cluster_examples':sorted(lost)[:20],'loop_crosslink_or_file_length_error':False,'BPB_state_byte_37':b[37],'read_only':True,'not_a_full_fsck_or_repair':True},indent=2))
 assert not lost,'Unreferenced allocated clusters require review'
