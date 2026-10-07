"""Offline1080p RGB565 pattern only; never opens a device/register."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    image=Image.new('RGB',(1920,1080));draw=ImageDraw.Draw(image)
    colors=[(255,255,255),(255,255,0),(0,255,255),(0,255,0),(255,0,255),(255,0,0),(0,0,255),(0,0,0)]
    for i,c in enumerate(colors):draw.rectangle((i*240,0,(i+1)*240-1,799),fill=c)
    for x in range(0,1920,120):draw.line((x,0,x,799),fill=(100,100,100),width=1)
    for y in range(0,800,100):draw.line((0,y,1919,y),fill=(100,100,100),width=1)
    for x in range(1920):
        c=x*255//1919;draw.line((x,800,x,919),fill=(c,c,c))
    draw.rectangle((0,920,1919,1079),fill=(20,20,20))
    draw.text((40,950),'HDMI TARGET 1920x1080 @60Hz / RGB565 LE',fill='white',font_size=36)
    draw.text((40,1000),'OFFLINE TEST PATTERN - NOT A SCREEN CAPTURE',fill='yellow',font_size=30)
    draw.rectangle((0,0,1919,1079),outline='white',width=4)
    rgb=np.asarray(image,dtype=np.uint16)
    packed=((rgb[:,:,0]>>3)<<11)|((rgb[:,:,1]>>2)<<5)|(rgb[:,:,2]>>3)
    data=packed.astype('<u2').tobytes();assert len(data)==4147200
    (args.output/'pattern.rgb565le').write_bytes(data);image.save(args.output/'pattern.png')
    info={'scope':'offline_CPU_only_no_HDMI_writes','width':1920,'height':1080,'target_refresh_hz':60,'format':'RGB565LE',
          'logical_stride':3840,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'hardware_stride_and_region_verified':False}
    (args.output/'pattern.json').write_bytes((json.dumps(info,indent=2)+'\n').encode());print(info)

if __name__=='__main__':main()
