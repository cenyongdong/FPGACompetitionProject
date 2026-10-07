// Query-only V4L2 probe. Never S_FMT/REQBUFS/QBUF/STREAMON, mmap or SDK open.
#include <linux/videodev2.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
static std::string quote(const char*p,size_t n){std::ostringstream out;out<<'"';for(size_t i=0;i<n&&p[i];++i){unsigned char c=p[i];if(c=='"'||c=='\\')out<<'\\';if(c>=32&&c<127)out<<c;else out<<'?';}out<<'"';return out.str();}
static int call(int fd,unsigned long command,void*p){int r;do{r=ioctl(fd,command,p);}while(r<0&&errno==EINTR);return r;}
int main(int argc,char**argv){try{
    if(argc!=2||std::string(argv[1]).rfind("/dev/video",0)!=0)throw std::runtime_error("Expected explicit /dev/video node");
    int fd=open(argv[1],O_RDONLY|O_NONBLOCK|O_CLOEXEC);if(fd<0)throw std::runtime_error("Cannot open query node");
    struct Closer{int fd;~Closer(){close(fd);}}closer{fd};v4l2_capability cap{};if(call(fd,VIDIOC_QUERYCAP,&cap)<0)throw std::runtime_error("QUERYCAP failed");
    std::cout<<"{\"scope\":\"query_only_no_configuration_or_stream\",\"node\":"<<quote(argv[1],128)<<",\"driver\":"<<quote(reinterpret_cast<char*>(cap.driver),sizeof(cap.driver))<<",\"card\":"<<quote(reinterpret_cast<char*>(cap.card),sizeof(cap.card))<<",\"version\":"<<cap.version<<",\"capabilities\":"<<cap.capabilities<<",\"device_caps\":"<<cap.device_caps<<",\"formats\":[";
    bool first=true;for(uint32_t type:{uint32_t(V4L2_BUF_TYPE_VIDEO_OUTPUT),uint32_t(V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE),uint32_t(V4L2_BUF_TYPE_VIDEO_CAPTURE),uint32_t(V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE)}){
        for(uint32_t i=0;i<64;++i){v4l2_fmtdesc f{};f.type=type;f.index=i;if(call(fd,VIDIOC_ENUM_FMT,&f)<0){if(errno==EINVAL)break;throw std::runtime_error("ENUM_FMT failed");}if(i==63)throw std::runtime_error("Unexpected format count");
            if(!first)std::cout<<',';first=false;char fourcc[5]={char(f.pixelformat&255),char((f.pixelformat>>8)&255),char((f.pixelformat>>16)&255),char((f.pixelformat>>24)&255),0};
            std::cout<<"{\"type\":"<<type<<",\"index\":"<<i<<",\"fourcc\":"<<quote(fourcc,4)<<",\"pixel_format\":"<<f.pixelformat<<",\"flags\":"<<f.flags<<",\"description\":"<<quote(reinterpret_cast<char*>(f.description),sizeof(f.description))<<",\"frame_sizes\":[";
            bool size_first=true;for(uint32_t j=0;j<64;++j){v4l2_frmsizeenum s{};s.index=j;s.pixel_format=f.pixelformat;if(call(fd,VIDIOC_ENUM_FRAMESIZES,&s)<0){if(errno==EINVAL||errno==ENOTTY)break;throw std::runtime_error("ENUM_FRAMESIZES failed");}
                if(j==63)throw std::runtime_error("Unexpected frame-size count");if(!size_first)std::cout<<',';size_first=false;
                if(s.type==V4L2_FRMSIZE_TYPE_DISCRETE)std::cout<<"{\"type\":\"discrete\",\"width\":"<<s.discrete.width<<",\"height\":"<<s.discrete.height<<'}';
                else if(s.type==V4L2_FRMSIZE_TYPE_STEPWISE||s.type==V4L2_FRMSIZE_TYPE_CONTINUOUS)std::cout<<"{\"type\":\"stepwise\",\"min_width\":"<<s.stepwise.min_width<<",\"max_width\":"<<s.stepwise.max_width<<",\"step_width\":"<<s.stepwise.step_width<<",\"min_height\":"<<s.stepwise.min_height<<",\"max_height\":"<<s.stepwise.max_height<<",\"step_height\":"<<s.stepwise.step_height<<'}';
                else throw std::runtime_error("Unknown frame-size enumeration");}
            std::cout<<"]}";}}
    std::cout<<"]}\n";return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
