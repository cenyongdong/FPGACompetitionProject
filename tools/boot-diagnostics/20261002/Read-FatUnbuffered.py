import ctypes as c, ctypes.wintypes as w, hashlib,json,pathlib,time
k=c.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.GetFileSizeEx.argtypes=[w.HANDLE,c.POINTER(c.c_longlong)];k.GetFileSizeEx.restype=w.BOOL
k.VirtualAlloc.argtypes=[c.c_void_p,c.c_size_t,w.DWORD,w.DWORD];k.VirtualAlloc.restype=c.c_void_p
k.VirtualFree.argtypes=[c.c_void_p,c.c_size_t,w.DWORD];k.VirtualFree.restype=w.BOOL
k.ReadFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p];k.ReadFile.restype=w.BOOL
k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
INVALID=c.c_void_p(-1).value
BLOCK=65536

def read_unbuffered(p):
 h=k.CreateFileW(str(p),0x80000000,1,None,3,0x20000000,None)
 if h==INVALID:raise c.WinError(c.get_last_error())
 buf=None
 try:
  size=c.c_longlong()
  if not k.GetFileSizeEx(h,c.byref(size)):raise c.WinError(c.get_last_error())
  buf=k.VirtualAlloc(None,BLOCK,0x3000,4)
  if not buf:raise c.WinError(c.get_last_error())
  assert buf%4096==0
  total=0;digest=hashlib.sha256();prefix=b'';zero_count=0
  while total<size.value:
   got=w.DWORD()
   if not k.ReadFile(h,buf,BLOCK,c.byref(got),None):raise c.WinError(c.get_last_error())
   if got.value==0:raise RuntimeError('Unexpected zero read before EOF')
   chunk=c.string_at(buf,min(got.value,size.value-total));digest.update(chunk);zero_count+=chunk.count(0)
   if total==0:prefix=chunk[:64]
   total+=len(chunk)
  return {'size':total,'sha256':digest.hexdigest(),'first_64_hex':prefix.hex(),'zero_bytes':zero_count,'entire_file_zero':zero_count==total}
 finally:
  if buf:k.VirtualFree(buf,0,0x8000)
  k.CloseHandle(h)

root=pathlib.Path(r'D:\FPGACompetitionProject\tools\boot-diagnostics\20261002')
check=pathlib.Path((root/'latest-remade-check.txt').read_text(encoding='utf-8-sig'))
reference=pathlib.Path(r'D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\位流\悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)\悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)\uEnv.txt')
control=read_unbuffered(reference)
control['buffered_sha256']=hashlib.sha256(reference.read_bytes()).hexdigest()
control['matches_buffered']=control['sha256']==control['buffered_sha256']
if not control['matches_buffered']:raise RuntimeError('Unbuffered reader control mismatch')
manifest=json.loads((root/'source-boot-manifest.json').read_text(encoding='utf-8-sig'))
results=[];start=time.monotonic()
for p in sorted(pathlib.Path('E:/').iterdir()):
 if not p.is_file():continue
 r={'name':p.name}
 try:
  r.update(read_unbuffered(p));r['source_matches']=[f['name_8_3'] for f in manifest['files'] if f['size']==r['size'] and f['sha256']==r['sha256']]
 except OSError as e:r['error']=str(e)
 results.append(r)
report={'scope':'read-only file data with FILE_FLAG_NO_BUFFERING, page-aligned 64KiB buffer','does_not_bypass':'file system metadata, device hardware caches, or reader controller','control':control,'elapsed_seconds':round(time.monotonic()-start,3),'files':results,'usb_reconnect':'not performed this time: user away from computer'}
(check/'unbuffered-file-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
