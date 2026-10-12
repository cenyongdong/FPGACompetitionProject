"""Fresh aligned-source variant; preserve natural-allocation r1 evidence."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def put(p,s):
    p=root/p
    if p.exists():assert p.read_text(encoding='utf-8')==s
    else:p.write_text(s,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=root/'.local/pose-v1-scratch-copy/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
sdk=(root/'software/pose_v1/src/scratch_copy_sdk.cpp').read_text(encoding='utf-8')
sdk=change(sdk,'std::array<xrt::Tensor,2> source;','std::array<xrt::Tensor,2> source;xrt::Tensor padding;')
sdk=change(sdk,'for(size_t i=0;i<2;++i){auto type=', 'for(size_t i=0;i<2;++i){if(i==1)padding=xrt::Tensor(xir::TensorType(xir::FloatType::FP32(),{8},xir::Layout("C"))).mallocOn(region);auto type=')
sdk=change(sdk,'}f<<"]}\\n";', '}f<<"],\\"padding_bytes\\":32,\\"padding_address\\":"<<padding.data().addr()<<",\\"source_alignment_required\\":64}\\n";')
needle='need(a!=b&&(a<b?b-a>=sizes[0]:a-b>=sizes[1]),"Scratch device sources overlap");'
sdk=change(sdk,needle,needle+'''
        need(a%64==0&&b%64==0,"Scratch source64 alignment differs");
        need(padding.hasData()&&(padding.data().ptype()==xrt::PtrType::ADDR||padding.data().ptype()==xrt::PtrType::BOTH)&&padding.memRegion().same_as(region)&&padding.dtype().bytes()==32,"Scratch padding identity differs");
        const auto pad=padding.data().addr();for(size_t i=0;i<2;++i){const auto address=source[i].data().addr();need(pad!=address&&(pad<address?address-pad>=32:pad-address>=sizes[i]),"Scratch padding overlaps source");}''')
put('software/pose_v1/src/scratch_copy_sdk_r2.cpp',sdk)
builder=(root/'tools/pose-v1/Build-ScratchCopy.ps1').read_text(encoding='utf-8').replace('mixed-20261010-scratch-copy-r1','mixed-20261010-scratch-copy-r2');put('tools/pose-v1/Build-ScratchCopyR2.ps1',builder)
review=(root/'tools/pose-v1/review_scratch_host.py').read_text(encoding='utf-8').replace('Build-ScratchCopy.ps1','Build-ScratchCopyR2.ps1');review=change(review,"'scratch_frozen_sources')","'scratch_frozen_sources','scratch_r2_frozen_sources')");put('tools/pose-v1/review_scratch_host_r2.py',review)
m['scratch_r2_frozen_sources']={'software/pose_v1/src/scratch_copy_sdk.cpp':g.sha(root/'software/pose_v1/src/scratch_copy_sdk.cpp')}
item=m['build_files'].pop('software/pose_v1/src/scratch_copy_sdk.cpp');m['build_files']['software/pose_v1/src/scratch_copy_sdk_r2.cpp']=dict(destination=item['destination'],sha256=g.sha(root/'software/pose_v1/src/scratch_copy_sdk_r2.cpp'))
for name in ('prepare_scratch_copy_r2.py','Build-ScratchCopyR2.ps1','review_scratch_host_r2.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ScratchCopyR2.ps1';m['scratch_copy']['source_alignment']=64;m['scratch_copy']['SDK_owned_padding_bytes']=32
out=root/'.local/pose-v1-scratch-copy/package-20261010-r2';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
