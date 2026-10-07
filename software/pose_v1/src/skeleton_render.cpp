#include "skeleton_render.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <sstream>
#include <iomanip>

namespace pose_v1::render {
namespace {
using Color=std::array<uint8_t,3>;
void need(bool yes,const char* s){if(!yes)throw std::runtime_error(s);}
constexpr double pi=3.14159265358979323846;
constexpr int left=24,right=926,top=96,bottom=658;
void pixel(std::vector<uint8_t>&im,int x,int y,Color c){if(x<0||x>=width||y<0||y>=height)return;size_t o=(size_t(y)*width+x)*3;std::copy(c.begin(),c.end(),im.begin()+o);}
void rect(std::vector<uint8_t>&im,int x0,int y0,int x1,int y1,Color c){for(int y=std::max(0,y0);y<std::min(height,y1);++y)for(int x=std::max(0,x0);x<std::min(width,x1);++x)pixel(im,x,y,c);}
int code(double x,double y){return (x<left?1:0)|(x>right?2:0)|(y<top?4:0)|(y>bottom?8:0);}
bool clip(double&x0,double&y0,double&x1,double&y1){
    for(int step=0;step<8;++step){int a=code(x0,y0),b=code(x1,y1);if(!(a|b))return true;if(a&b)return false;int c=a?a:b;double x=0,y=0;
        if(c&8){y=bottom;x=x0+(x1-x0)*(bottom-y0)/(y1-y0);}else if(c&4){y=top;x=x0+(x1-x0)*(top-y0)/(y1-y0);}
        else if(c&2){x=right;y=y0+(y1-y0)*(right-x0)/(x1-x0);}else{x=left;y=y0+(y1-y0)*(left-x0)/(x1-x0);}
        need(std::isfinite(x)&&std::isfinite(y),"Projection clipping failed");if(c==a){x0=x;y0=y;}else{x1=x;y1=y;}}
    throw std::runtime_error("Clipping did not converge");
}
void line(std::vector<uint8_t>&im,double a,double b,double c,double d,Color color,int radius=0){
    if(!clip(a,b,c,d))return;
    int x0=int(std::lround(a)),y0=int(std::lround(b)),x1=int(std::lround(c)),y1=int(std::lround(d));
    int dx=std::abs(x1-x0),sx=x0<x1?1:-1,dy=-std::abs(y1-y0),sy=y0<y1?1:-1,err=dx+dy;
    for(;;){rect(im,x0-radius,y0-radius,x0+radius+1,y0+radius+1,color);if(x0==x1&&y0==y1)break;int e=2*err;if(e>=dy){err+=dy;x0+=sx;}if(e<=dx){err+=dx;y0+=sy;}}
}
const std::map<char,std::array<uint8_t,7>> glyphs={
{'0',{14,17,19,21,25,17,14}},{'1',{4,12,4,4,4,4,14}},{'2',{14,17,1,2,4,8,31}},{'3',{30,1,1,14,1,1,30}},{'4',{2,6,10,18,31,2,2}},{'5',{31,16,16,30,1,1,30}},{'6',{14,16,16,30,17,17,14}},{'7',{31,1,2,4,8,8,8}},{'8',{14,17,17,14,17,17,14}},{'9',{14,17,17,15,1,1,14}},
{'A',{14,17,17,31,17,17,17}},{'B',{30,17,17,30,17,17,30}},{'C',{14,17,16,16,16,17,14}},{'D',{30,17,17,17,17,17,30}},{'E',{31,16,16,30,16,16,31}},{'F',{31,16,16,30,16,16,16}},{'G',{14,17,16,23,17,17,15}},{'H',{17,17,17,31,17,17,17}},{'I',{14,4,4,4,4,4,14}},{'J',{7,2,2,2,2,18,12}},{'K',{17,18,20,24,20,18,17}},{'L',{16,16,16,16,16,16,31}},{'M',{17,27,21,21,17,17,17}},{'N',{17,25,21,19,17,17,17}},{'O',{14,17,17,17,17,17,14}},{'P',{30,17,17,30,16,16,16}},{'Q',{14,17,17,17,21,18,13}},{'R',{30,17,17,30,20,18,17}},{'S',{15,16,16,14,1,1,30}},{'T',{31,4,4,4,4,4,4}},{'U',{17,17,17,17,17,17,14}},{'V',{17,17,17,17,17,10,4}},{'W',{17,17,17,21,21,21,10}},{'X',{17,17,10,4,10,17,17}},{'Y',{17,17,10,4,4,4,4}},{'Z',{31,1,2,4,8,16,31}},
{':',{0,4,4,0,4,4,0}},{'-',{0,0,0,31,0,0,0}},{'.',{0,0,0,0,0,6,6}},{'/',{1,2,2,4,8,8,16}},{' ',{0,0,0,0,0,0,0}}};
void text(std::vector<uint8_t>&im,int x,int y,const std::string&s,int scale,Color color){for(char c:s){auto g=glyphs.find(c);need(g!=glyphs.end(),"Unsupported render glyph");for(int row=0;row<7;++row)for(int col=0;col<5;++col)if(g->second[row]&(1<<(4-col)))rect(im,x+col*scale,y+row*scale,x+(col+1)*scale,y+(row+1)*scale,color);x+=6*scale;}}
size_t image_bytes(int w,int h){need(w>0&&h>0&&w<=4096&&h<=4096,"Invalid raster dimensions");return size_t(w)*size_t(h)*3;}
int floor256(int v){return v>=0?v/256:-((-v+255)/256);}
uint8_t clamp(int v){return uint8_t(std::clamp(v,0,255));}
}
std::array<double,2> project(double a,double b,double c){
    need(std::isfinite(a)&&std::isfinite(b)&&std::isfinite(c),"Non-finite coordinate");double x=a-1.75,y=b-1.75,z=-(c-3.4);
    double cy=std::cos(pi/6),sy=std::sin(pi/6),ce=std::cos(pi/9),se=std::sin(pi/9);
    return {460+220*(cy*x-sy*y),355-220*(ce*z-se*(sy*x+cy*y))};
}
Frame draw(const std::array<float,100>&scores,const std::array<float,4200>&poses,uint64_t id,Status status){
    auto begin=std::chrono::steady_clock::now();for(float v:scores)need(std::isfinite(v),"Non-finite candidate score");for(float v:poses)need(std::isfinite(v),"Non-finite candidate pose");
    need(status==Status::Result||status==Status::NoInput||status==Status::Stopped,"Unknown result status");Frame f;f.frame_id=id;f.top_index=std::max_element(scores.begin(),scores.end())-scores.begin();f.score=scores[f.top_index];std::copy_n(poses.begin()+f.top_index*42,42,f.selected_raw.begin());
    f.rgb.resize(size_t(width)*height*3);for(int y=0;y<height;++y){uint8_t v=uint8_t(16+y*10/height);for(int x=0;x<width;++x)pixel(f.rgb,x,y,{v,uint8_t(v+5),uint8_t(v+14)});}
    rect(f.rgb,944,0,width,height,{25,35,49});rect(f.rgb,0,0,944,78,{20,30,44});text(f.rgb,28,27,"WIFI 3D POSE",4,{229,237,247});
    text(f.rgb,966,32,"PS/NPU",4,{93,207,235});text(f.rgb,966,102,"FRAME",2,{167,184,204});text(f.rgb,966,128,std::to_string(id),2,{236,241,247});
    text(f.rgb,966,188,"TOP SLOT",2,{167,184,204});text(f.rgb,966,215,std::to_string(f.top_index),3,{236,241,247});std::ostringstream score;score<<std::fixed<<std::setprecision(4)<<f.score;
    // Scores are finite but arbitrary; show an explicit range message if text is too wide.
    std::string shown=score.str();if(shown.size()>15)shown="OUT OF RANGE";
    text(f.rgb,966,274,"SCORE",2,{167,184,204});text(f.rgb,966,302,shown,2,{255,122,112});text(f.rgb,966,364,"STATUS",2,{167,184,204});text(f.rgb,966,392,status==Status::Result?"RESULT":status==Status::NoInput?"NO INPUT":"STOPPED",2,{130,221,164});
    text(f.rgb,966,470,"14 JOINTS",2,{167,184,204});text(f.rgb,966,514,"MODEL UNITS",2,{167,184,204});text(f.rgb,966,552,"NO CALIBRATION",2,{167,184,204});text(f.rgb,28,687,"HIGHEST SCORE / NO TRACKING / FIXED VIEW",2,{143,163,186});
    Color grid{48,63,78};for(double v=0.25;v<=3.75;v+=0.5){auto a=project(v,0.25,4.2),b=project(v,3.75,4.2);line(f.rgb,a[0],a[1],b[0],b[1],grid);a=project(0.25,v,4.2);b=project(3.75,v,4.2);line(f.rgb,a[0],a[1],b[0],b[1],grid);}
    auto origin=project(0.5,0.5,4.2);const std::array<std::array<double,3>,3> end{{{1.1,0.5,4.2},{0.5,1.1,4.2},{0.5,0.5,3.6}}};const std::array<Color,3> axis{{{222,121,112},{110,199,142},{104,168,237}}};
    for(size_t i=0;i<3;++i){auto p=project(end[i][0],end[i][1],end[i][2]);line(f.rgb,origin[0],origin[1],p[0],p[1],axis[i],1);if(!code(p[0],p[1]))text(f.rgb,int(p[0])+4,int(p[1])-14,i==2?"-C2":i==0?"C0":"C1",2,axis[i]);}
    for(size_t i=0;i<14;++i){f.projected[i]=project(f.selected_raw[i*3],f.selected_raw[i*3+1],f.selected_raw[i*3+2]);if(code(f.projected[i][0],f.projected[i][1]))++f.clipped_joints;}
    if(status==Status::Result){for(auto b:bones){auto a=f.projected[b[0]],c=f.projected[b[1]];line(f.rgb,a[0],a[1],c[0],c[1],{255,91,94},1);}
        for(size_t i=0;i<14;++i){auto p=f.projected[i];if(code(p[0],p[1]))continue;int x=int(std::lround(p[0])),y=int(std::lround(p[1]));for(int dy=-4;dy<=4;++dy)for(int dx=-4;dx<=4;++dx)if(dx*dx+dy*dy<=16)pixel(f.rgb,x+dx,y+dy,{255,204,185});text(f.rgb,x+7,y-10,std::to_string(i),1,{236,231,224});}}
    f.render_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();return f;
}
std::vector<uint8_t> rgb565_le(const std::vector<uint8_t>&rgb,int w,int h){need(rgb.size()==image_bytes(w,h),"RGB byte count differs");std::vector<uint8_t> out(size_t(w)*h*2);
    for(size_t i=0;i<size_t(w)*h;++i){uint16_t v=uint16_t((rgb[i*3]>>3)<<11)|uint16_t((rgb[i*3+1]>>2)<<5)|(rgb[i*3+2]>>3);out[i*2]=v&255;out[i*2+1]=v>>8;}return out;}
std::vector<uint8_t> yuv420sp(const std::vector<uint8_t>&rgb,int w,int h,bool nv21){need(rgb.size()==image_bytes(w,h)&&w%2==0&&h%2==0,"Invalid YUV420 source dimensions/bytes");size_t count=size_t(w)*h;std::vector<uint8_t> out(count*3/2);
    for(size_t i=0;i<count;++i){int r=rgb[i*3],g=rgb[i*3+1],b=rgb[i*3+2];out[i]=clamp(floor256(66*r+129*g+25*b+128)+16);}
    for(int y=0;y<h;y+=2)for(int x=0;x<w;x+=2){int r=0,g=0,b=0;for(int dy=0;dy<2;++dy)for(int dx=0;dx<2;++dx){size_t i=(size_t(y+dy)*w+x+dx)*3;r+=rgb[i];g+=rgb[i+1];b+=rgb[i+2];}r=(r+2)/4;g=(g+2)/4;b=(b+2)/4;
        uint8_t u=clamp(floor256(-38*r-74*g+112*b+128)+128),v=clamp(floor256(112*r-94*g-18*b+128)+128);size_t i=count+size_t(y/2)*w+x;out[i]=nv21?v:u;out[i+1]=nv21?u:v;}
    return out;
}
}
