"""Independent NumPy projection/format review and lossless RGB preview export."""
import argparse,json,hashlib,struct,zlib
from pathlib import Path
import numpy as np
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ppm(p):
    raw=p.read_bytes();magic,size,maximum,pixels=raw.split(b'\n',3);assert magic==b'P6' and maximum==b'255'
    w,h=map(int,size.split());assert (w,h)==(1280,720) and len(pixels)==w*h*3
    return np.frombuffer(pixels,np.uint8).reshape(h,w,3)
def formats(folder,stem,rgb):
    h,w,_=rgb.shape;r,g,b=np.moveaxis(rgb.astype(np.int32),-1,0)
    expected=(((r>>3)<<11)|((g>>2)<<5)|(b>>3)).astype('<u2').tobytes();assert (folder/(stem+'.rgb565le')).read_bytes()==expected
    y=((66*r+129*g+25*b+128)//256+16).clip(0,255).astype(np.uint8)
    a=rgb.astype(np.int32).reshape(h//2,2,w//2,2,3).sum(axis=(1,3));a=(a+2)//4;r,g,b=np.moveaxis(a,-1,0)
    u=((-38*r-74*g+112*b+128)//256+128).clip(0,255).astype(np.uint8)
    v=((112*r-94*g-18*b+128)//256+128).clip(0,255).astype(np.uint8)
    for nv21 in [False,True]:
        uv=np.stack((v,u) if nv21 else (u,v),axis=-1);suffix='.nv21' if nv21 else '.nv12';assert (folder/(stem+suffix)).read_bytes()==y.tobytes()+uv.tobytes()
def png(rgb,path):
    h,w,_=rgb.shape
    def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    rows=b''.join(b'\0'+row.tobytes() for row in rgb)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b''))
def review(folder,input_folder,catalog):
    records=[];names=[(s.split()[0],int(s.split()[1])) for s in catalog.read_text().splitlines()] if catalog else [('synthetic',999),('clipped',1000),('no-input',1001),('stopped',1002)]
    for stem,frame in names:
        m=json.loads((folder/(stem+'.json')).read_text());assert m['frame_id']==frame and np.isfinite(m['render_ms']) and m['render_ms']>=0
        points=np.asarray(m['selected_raw'],np.float64).reshape(14,3)
        if input_folder:
            s=np.fromfile(input_folder/(stem+'.scores.f32'),dtype='<f4');p=np.fromfile(input_folder/(stem+'.poses.f32'),dtype='<f4').reshape(100,14,3);index=int(np.argmax(s))
            assert m['top_index']==index and np.array_equal(points.astype('<f4'),p[index]) and np.float32(m['score'])==s[index]
        elif stem=='synthetic':assert m['top_index']==3
        x,y,z=(points-np.array([1.75,1.75,3.4])).T;z=-z;cy,sy=np.cos(np.pi/6),np.sin(np.pi/6);ce,se=np.cos(np.pi/9),np.sin(np.pi/9)
        projected=np.stack((460+220*(cy*x-sy*y),355-220*(ce*z-se*(sy*x+cy*y))),axis=-1)
        assert np.allclose(projected,m['projected'],rtol=1e-14,atol=1e-9),'Projection mismatch'
        clipped=((projected[:,0]<24)|(projected[:,0]>926)|(projected[:,1]<96)|(projected[:,1]>658)).sum();assert m['clipped_joints']==int(clipped)
        rgb=ppm(folder/(stem+'.ppm'));formats(folder,stem,rgb)
        records.append(dict(stem=stem,frame_id=frame,top_index=m['top_index'],clipped=int(clipped),rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),render_ms=m['render_ms'],three_format_conversion_ms=m['three_format_conversion_ms']))
    if not input_folder:
        s=json.loads((folder/'self-test.json').read_text());assert s['status']=='passed' and s['rejections']==8
        rgb=np.frombuffer((folder/'colors.rgb24').read_bytes(),np.uint8).reshape(2,2,3);formats(folder,'colors',rgb)
        assert (folder/'colors.rgb565le').read_bytes()==bytes.fromhex('00f8e0071f00ffff')
        assert (folder/'colors.nv12').read_bytes()==bytes([82,144,41,235,128,128])
    return dict(status='independent_render_review_passed',frames=records,all_formats_bitwise_numpy=True,raw_selected_coordinates_preserved=True,physical_calibration=False,hardware_output_tested=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,required=True);p.add_argument('--input',type=Path);p.add_argument('--catalog',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--preview',type=Path)
    a=p.parse_args();assert not a.output.exists();r=review(a.results,a.input,a.catalog);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if a.preview:
        assert not a.preview.exists();a.preview.mkdir(parents=True)
        for item in r['frames'][:3]:png(ppm(a.results/(item['stem']+'.ppm')),a.preview/(item['stem']+'.png'))
    print('Independent render review passed:',len(r['frames']))
