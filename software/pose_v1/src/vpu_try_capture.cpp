// Metadata-only idle-context TRY_FMT; noS_FMT/REQBUFS/stream/Icraft/MMIO.
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <iostream>
int main() {
    int fd=open("/dev/video0",O_RDONLY|O_NONBLOCK|O_CLOEXEC);
    if(fd<0) return 1;
    std::cout<<"{\"scope\":\"idle_TRY_FMT_only\",\"single_capture\":[";
    for(unsigned i=0;i<2;++i) {
        if(i) std::cout<<',';
        v4l2_format f{};f.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        f.fmt.pix.width=1280;f.fmt.pix.height=720;f.fmt.pix.pixelformat=i ? V4L2_PIX_FMT_HEVC:V4L2_PIX_FMT_H264;
        f.fmt.pix.field=V4L2_FIELD_NONE;f.fmt.pix.sizeimage=2097152;
        int r=ioctl(fd,VIDIOC_TRY_FMT,&f);int e=r<0 ? errno:0;
        std::cout<<"{\"requested\":\""<<(i ? "HEVC":"H264")<<"\",\"result\":"<<r<<",\"errno\":"<<e
                 <<",\"returned_pixel_format\":"<<f.fmt.pix.pixelformat<<",\"width\":"<<f.fmt.pix.width<<",\"height\":"<<f.fmt.pix.height<<",\"sizeimage\":"<<f.fmt.pix.sizeimage<<'}';
    }
    std::cout<<"],\"streamed\":false}"<<std::endl;close(fd);return 0;
}
