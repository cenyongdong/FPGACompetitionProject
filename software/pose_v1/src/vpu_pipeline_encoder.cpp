// Isolated, finite V4L2 encoder test. No Icraft, HDMI, registers or camera MMU.
#include "vpu_pipeline_encoder.hpp"
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr unsigned W=1280, H=720, FPS=10;
constexpr auto IN=V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE;
constexpr auto OUT=V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
// Actual vendor reference mvx-v4l2-controls.h: Q16 frame rate.
constexpr unsigned MVE_FRAME_RATE=V4L2_CTRL_CLASS_MPEG+0x2000;
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int call(int fd,unsigned long op,void* p) {
    int r; do { r=ioctl(fd,op,p); } while(r<0 && errno==EINTR); return r;
}
void checked(int fd,unsigned long op,void* p,const char* name) {
    if(call(fd,op,p)<0) throw std::runtime_error(std::string(name)+": "+strerror(errno));
}
std::string fourcc(unsigned v) { std::string s; for(int i=0;i<4;++i) s+=char((v>>(8*i))&255); return s; }
void format(std::ostream& log,const v4l2_format& f) {
    const auto& p=f.fmt.pix_mp;
    log<<"{\"event\":\"format\",\"type\":"<<f.type<<",\"fourcc\":\""<<fourcc(p.pixelformat)
       <<"\",\"width\":"<<p.width<<",\"height\":"<<p.height<<",\"planes\":"<<unsigned(p.num_planes)
       <<",\"field\":"<<p.field<<",\"colorspace\":"<<p.colorspace<<",\"ycbcr_enc\":"<<unsigned(p.ycbcr_enc)
       <<",\"quantization\":"<<unsigned(p.quantization)<<",\"xfer_func\":"<<unsigned(p.xfer_func)<<",\"layout\":[";
    for(unsigned i=0;i<p.num_planes;++i) {
        if(i) log<<',';
        log<<"{\"stride\":"<<p.plane_fmt[i].bytesperline<<",\"size\":"<<p.plane_fmt[i].sizeimage<<'}';
    }
    log<<"]}"<<std::endl;
}
struct Plane { void* ptr=MAP_FAILED; unsigned size=0; unsigned mmapCookie=0; };
struct Queue {
    int fd; v4l2_buf_type type; unsigned planes; bool streaming=false;
    std::ostream* trace=nullptr;
    std::vector<std::vector<Plane>> buffers;
    std::vector<bool> ownedByDriver;
    Queue(int f,v4l2_buf_type t,unsigned p):fd(f),type(t),planes(p) {}
    ~Queue() {
        if(streaming) {
            int result=call(fd,VIDIOC_STREAMOFF,&type); int error=result<0 ? errno:0;
            if(trace) *trace<<"{\"event\":\"abort_streamoff\",\"type\":"<<type<<",\"result\":"<<result<<",\"errno\":"<<error<<"}"<<std::endl;
        }
        for(auto& b:buffers) for(auto& p:b) if(p.ptr!=MAP_FAILED) munmap(p.ptr,p.size);
        if(!buffers.empty()) { v4l2_requestbuffers r{}; r.type=type; r.memory=V4L2_MEMORY_MMAP; call(fd,VIDIOC_REQBUFS,&r); }
    }
    void allocate(std::ostream& log) {
        trace=&log;
        v4l2_requestbuffers r{}; r.type=type; r.memory=V4L2_MEMORY_MMAP; r.count=6;
        checked(fd,VIDIOC_REQBUFS,&r,"REQBUFS"); require(r.count>=2 && r.count<=16,"unexpected buffer count");
        buffers.resize(r.count);
        ownedByDriver.resize(r.count,false);
        for(unsigned i=0;i<r.count;++i) {
            v4l2_buffer b{}; v4l2_plane p[VIDEO_MAX_PLANES]{};
            b.type=type; b.memory=V4L2_MEMORY_MMAP; b.index=i; b.length=planes; b.m.planes=p;
            checked(fd,VIDIOC_QUERYBUF,&b,"QUERYBUF"); require(b.length==planes,"query plane count changed");
            describe("querybuf",b,p);
            buffers[i].resize(planes);
            for(unsigned j=0;j<planes;++j) {
                require(p[j].length>0 && p[j].length<=16*1024*1024,"unbounded buffer");
                auto& q=buffers[i][j]; q.size=p[j].length;q.mmapCookie=p[j].m.mem_offset;
                q.ptr=mmap(nullptr,q.size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,p[j].m.mem_offset);
                require(q.ptr!=MAP_FAILED,"mmap failed");
                log<<"{\"event\":\"buffer\",\"type\":"<<type<<",\"index\":"<<i<<",\"plane\":"<<j<<",\"length\":"<<q.size<<",\"mmap_cookie\":"<<p[j].m.mem_offset<<",\"data_offset\":"<<p[j].data_offset<<"}"<<std::endl;
            }
        }
    }
    void describe(const char* event,const v4l2_buffer& b,const v4l2_plane* p) const {
        if(!trace) return;
        *trace<<"{\"event\":\""<<event<<"\",\"type\":"<<b.type<<",\"index\":"<<b.index<<",\"memory\":"<<b.memory
              <<",\"flags\":"<<b.flags<<",\"field\":"<<b.field<<",\"sequence\":"<<b.sequence
              <<",\"pts_us\":"<<b.timestamp.tv_sec*1000000LL+b.timestamp.tv_usec<<",\"planes\":[";
        for(unsigned j=0;j<b.length;++j) {
            if(j) *trace<<',';
            *trace<<"{\"length\":"<<p[j].length<<",\"bytesused\":"<<p[j].bytesused<<",\"data_offset\":"<<p[j].data_offset<<",\"mmap_cookie\":"<<p[j].m.mem_offset<<'}';
        }
        *trace<<"]}"<<std::endl;
    }
    void queue(unsigned i,const std::vector<unsigned>& used,unsigned frame=0) {
        require(i<buffers.size() && used.size()==planes,"queue bounds");
        require(!ownedByDriver[i],"buffer still owned by driver before queue");
        v4l2_buffer b{}; v4l2_plane p[VIDEO_MAX_PLANES]{};
        b.type=type; b.memory=V4L2_MEMORY_MMAP; b.index=i; b.length=planes; b.m.planes=p;
        b.field=V4L2_FIELD_NONE; b.timestamp.tv_sec=frame/FPS; b.timestamp.tv_usec=(frame%FPS)*100000;
        for(unsigned j=0;j<planes;++j) {
            require(used[j]<=buffers[i][j].size,"queue size");
            p[j].length=buffers[i][j].size;p[j].bytesused=used[j];
            // Preserve QUERYBUF's opaque cookie as the shipped client does.
            // No physical address inference or allocation/capacity change.
            p[j].m.mem_offset=buffers[i][j].mmapCookie;
        }
        describe("qbuf_enter",b,p);
        checked(fd,VIDIOC_QBUF,&b,"QBUF");
        ownedByDriver[i]=true;
        describe("qbuf_return",b,p);
    }
    bool dequeue(v4l2_buffer& b,v4l2_plane* p) {
        b={}; b.type=type; b.memory=V4L2_MEMORY_MMAP; b.length=planes; b.m.planes=p;
        if(call(fd,VIDIOC_DQBUF,&b)<0) {
            if(errno==EAGAIN) return false;
            if(trace) *trace<<"{\"event\":\"dqbuf_error\",\"type\":"<<type<<",\"errno\":"<<errno<<"}"<<std::endl;
            throw std::runtime_error(std::string("DQBUF: ")+strerror(errno));
        }
        require(b.index<buffers.size() && b.length==planes,"dequeue bounds");
        describe("dqbuf",b,p);
        require(ownedByDriver[b.index],"dequeued buffer not owned by driver");
        ownedByDriver[b.index]=false;
        require(!(b.flags&V4L2_BUF_FLAG_ERROR),"driver buffer error"); return true;
    }
    void start() {
        checked(fd,VIDIOC_STREAMON,&type,"STREAMON"); streaming=true;
        if(trace) *trace<<"{\"event\":\"streamon\",\"type\":"<<type<<"}"<<std::endl;
    }
    void stop() {
        checked(fd,VIDIOC_STREAMOFF,&type,"STREAMOFF"); streaming=false;
        if(trace) *trace<<"{\"event\":\"streamoff\",\"type\":"<<type<<"}"<<std::endl;
    }
};
struct Device { int fd=-1; ~Device(){ if(fd>=0) close(fd); } };
void control(int fd,unsigned id,int value,std::ostream& log) {
    v4l2_queryctrl q{}; q.id=id; checked(fd,VIDIOC_QUERYCTRL,&q,"QUERYCTRL");
    require(!(q.flags&V4L2_CTRL_FLAG_DISABLED) && value>=q.minimum && value<=q.maximum,"control unsupported/range");
    v4l2_control c{}; c.id=id; c.value=value; checked(fd,VIDIOC_S_CTRL,&c,"S_CTRL");
    checked(fd,VIDIOC_G_CTRL,&c,"G_CTRL"); require(c.value==value,"control readback differs");
    log<<"{\"event\":\"control\",\"id\":"<<id<<",\"value\":"<<c.value<<"}"<<std::endl;
}
}
namespace pose::video {
void validateOwnedFrame(const OwnedFrame& frame,unsigned requestedId) {
    require(frame.nv12.size()==nv12FrameBytes,"producer NV12 size differs");
    require(frame.encodedId==requestedId && requestedId<60,"producer encoded identity differs");
    require(frame.generatedNs>0,"producer generation timestamp missing");
}
EncodeResult encodeNv12Producer(const std::filesystem::path& dest,const EncodeOptions& options,FrameProducer producer,PacketConsumer consumer,unsigned primeInputs) {
    require(options.allowVpuStream,"explicit VPU authorization required");
    require(options.frameCount>=2 && options.frameCount<=60,"frame count outside2..60");
    require(primeInputs==2 || primeInputs==6,"supported prime count is2 or6");
    require(bool(producer) && bool(consumer),"producer/consumer missing before device access");
    require(!std::filesystem::exists(dest),"output exists; preserve and stop"); std::filesystem::create_directory(dest);
    std::ofstream log(dest/"events.jsonl"); require(bool(log),"log open failed");
    Device d; d.fd=open("/dev/video0",O_RDWR|O_NONBLOCK|O_CLOEXEC); require(d.fd>=0,"open video0 failed");
    v4l2_capability cap{}; checked(d.fd,VIDIOC_QUERYCAP,&cap,"QUERYCAP");
    require(std::string(reinterpret_cast<char*>(cap.driver))=="mvx","driver identity changed");
    require(cap.device_caps&V4L2_CAP_VIDEO_M2M_MPLANE,"missing M2M MPLANE");
    log<<"{\"event\":\"identity\",\"driver\":\"mvx\",\"version\":"<<cap.version<<",\"device_caps\":"<<cap.device_caps<<"}"<<std::endl;
    v4l2_format coded{}; coded.type=OUT; coded.fmt.pix_mp.pixelformat=V4L2_PIX_FMT_H264;
    coded.fmt.pix_mp.width=W; coded.fmt.pix_mp.height=H; coded.fmt.pix_mp.num_planes=1; coded.fmt.pix_mp.plane_fmt[0].sizeimage=2*1024*1024;
    checked(d.fd,VIDIOC_S_FMT,&coded,"S_FMT H264");
    v4l2_format raw{}; raw.type=IN; auto& rp=raw.fmt.pix_mp;
    rp.width=W; rp.height=H; rp.pixelformat=V4L2_PIX_FMT_NV12; rp.field=V4L2_FIELD_NONE;
    rp.colorspace=V4L2_COLORSPACE_SMPTE170M; rp.ycbcr_enc=V4L2_YCBCR_ENC_601;
    rp.quantization=V4L2_QUANTIZATION_LIM_RANGE; rp.xfer_func=V4L2_XFER_FUNC_709;
    checked(d.fd,VIDIOC_S_FMT,&raw,"S_FMT NV12");
    // This MVX driver leaves coded size at 2x2 when CAPTURE precedes raw.
    // Reapply coded format after raw as the shipped vendor Encoder does,
    // then read both formats again; never accept a mismatching size.
    coded.fmt.pix_mp.width=W; coded.fmt.pix_mp.height=H;
    coded.fmt.pix_mp.colorspace=V4L2_COLORSPACE_SMPTE170M;
    coded.fmt.pix_mp.ycbcr_enc=V4L2_YCBCR_ENC_601;
    coded.fmt.pix_mp.quantization=V4L2_QUANTIZATION_LIM_RANGE;
    coded.fmt.pix_mp.xfer_func=V4L2_XFER_FUNC_709;
    checked(d.fd,VIDIOC_S_FMT,&coded,"S_FMT H264 after NV12");
    checked(d.fd,VIDIOC_G_FMT,&raw,"G_FMT NV12"); checked(d.fd,VIDIOC_G_FMT,&coded,"G_FMT H264");
    format(log,raw); format(log,coded);
    require(rp.width==W && rp.height==H && rp.pixelformat==V4L2_PIX_FMT_NV12 && rp.field==V4L2_FIELD_NONE,"raw format changed");
    require(rp.colorspace==V4L2_COLORSPACE_SMPTE170M && rp.ycbcr_enc==V4L2_YCBCR_ENC_601 && rp.quantization==V4L2_QUANTIZATION_LIM_RANGE,"raw colorimetry differs");
    require(rp.num_planes==1 || rp.num_planes==2,"unsupported NV12 plane layout");
    require(coded.fmt.pix_mp.pixelformat==V4L2_PIX_FMT_H264 && coded.fmt.pix_mp.num_planes==1 && coded.fmt.pix_mp.width==W && coded.fmt.pix_mp.height==H,"coded format changed");
    require(coded.fmt.pix_mp.colorspace==rp.colorspace && coded.fmt.pix_mp.ycbcr_enc==rp.ycbcr_enc && coded.fmt.pix_mp.quantization==rp.quantization && coded.fmt.pix_mp.xfer_func==rp.xfer_func,"coded colorimetry differs");
    const unsigned ys=rp.plane_fmt[0].bytesperline;
    const unsigned uvs=rp.num_planes==1 ? ys:rp.plane_fmt[1].bytesperline;
    require(ys>=W && uvs>=W && ys<=8192 && uvs<=8192,"unsupported stride");
    const unsigned ybytes=ys*H, uvbytes=uvs*(H/2);
    std::vector<unsigned> used=rp.num_planes==1 ? std::vector<unsigned>{ybytes+uvbytes}:std::vector<unsigned>{ybytes,uvbytes};
    for(unsigned i=0;i<used.size();++i) require(rp.plane_fmt[i].sizeimage>=used[i],"format too small");
    control(d.fd,MVE_FRAME_RATE,FPS<<16,log);
    control(d.fd,V4L2_CID_MPEG_VIDEO_BITRATE,2000000,log);
    control(d.fd,V4L2_CID_MPEG_VIDEO_H264_PROFILE,V4L2_MPEG_VIDEO_H264_PROFILE_BASELINE,log);
    v4l2_encoder_cmd trycmd{}; trycmd.cmd=V4L2_ENC_CMD_STOP;
    checked(d.fd,VIDIOC_TRY_ENCODER_CMD,&trycmd,"TRY_ENCODER_CMD STOP");
    std::ofstream stream(dest/"video.h264",std::ios::binary),submitted(dest/"submitted.nv12",std::ios::binary);
    require(bool(stream) && bool(submitted),"data files open failed");
    Queue in(d.fd,IN,rp.num_planes),out(d.fd,OUT,1); in.allocate(log); out.allocate(log);
    for(const auto& b:in.buffers) for(unsigned j=0;j<used.size();++j) require(b[j].size>=used[j],"mapped raw buffer too small");
    unsigned queued=0,returned=0; bool draining=false,last=false; size_t total=0;
    std::chrono::steady_clock::duration producerPaused{};
    std::vector<unsigned char> src(size_t(W)*H*3/2);
    auto submit=[&](unsigned idx) {
        require(!in.ownedByDriver[idx],"CPU attempted write while driver owns input");
        const bool streaming=in.streaming && out.streaming;
        log<<"{\"event\":\"producer_enter\",\"frame\":"<<queued<<",\"VPU_streaming\":"<<(streaming?"true":"false")<<"}"<<std::endl;
        const auto producerBegin=std::chrono::steady_clock::now();
        auto frame=producer(queued);validateOwnedFrame(frame,queued);
        const auto producerElapsed=std::chrono::steady_clock::now()-producerBegin;
        require(producerElapsed<std::chrono::seconds(60),"producer exceeded60s diagnostic bound");
        if(streaming)producerPaused+=producerElapsed;
        log<<"{\"event\":\"producer_duration\",\"frame\":"<<queued<<",\"nanoseconds\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(producerElapsed).count()<<"}"<<std::endl;
        src=std::move(frame.nv12);
        submitted.write(reinterpret_cast<const char*>(src.data()),src.size());require(bool(submitted),"submitted content write failed");
        log<<"{\"event\":\"source_frame\",\"encoded_id\":"<<frame.encodedId<<",\"source_frame_id\":"<<frame.sourceFrame
           <<",\"invocation\":"<<frame.invocation<<",\"generated_ns\":"<<frame.generatedNs<<",\"repeated_source\":"<<(frame.repeatedSource?"true":"false")
           <<",\"inference_result\":"<<(frame.inferenceResult?"true":"false")<<"}"<<std::endl;
        auto& b=in.buffers[idx];
        for(auto& p:b) memset(p.ptr,0,p.size);
        auto* y=static_cast<unsigned char*>(b[0].ptr);
        auto* uv=rp.num_planes==1 ? y+ybytes:static_cast<unsigned char*>(b[1].ptr);
        for(unsigned row=0;row<H;++row) memcpy(y+row*ys,src.data()+row*W,W);
        for(unsigned row=0;row<H/2;++row) memcpy(uv+row*uvs,src.data()+size_t(W)*H+row*W,W);
        bool hostEqual=true;
        for(unsigned row=0;row<H;++row) hostEqual &= memcmp(y+row*ys,src.data()+row*W,W)==0;
        for(unsigned row=0;row<H/2;++row) hostEqual &= memcmp(uv+row*uvs,src.data()+size_t(W)*H+row*W,W)==0;
        log<<"{\"event\":\"host_copy_check\",\"frame\":"<<queued<<",\"equal\":"<<(hostEqual ? "true":"false")<<"}"<<std::endl;
        require(hostEqual,"Host mapped input differs from current frame");
        in.queue(idx,used,queued);
        log<<"{\"event\":\"input_queued\",\"frame\":"<<queued<<",\"pts_us\":"<<queued*100000<<",\"index\":"<<idx<<"}"<<std::endl;
        ++queued;
    };
    for(unsigned i=0;i<out.buffers.size();++i) out.queue(i,{0});
    log<<"{\"event\":\"input_prime_policy\",\"allocated_buffers\":"<<in.buffers.size()<<",\"prime_count\":"<<primeInputs<<"}"<<std::endl;
    for(unsigned i=0;i<in.buffers.size() && i<primeInputs && queued<options.frameCount;++i) submit(i);
    out.start(); in.start();
    auto began=std::chrono::steady_clock::now(); auto progress=began;
    while(!last || returned<options.frameCount) {
        bool moved=false;
        if(!last) {
            v4l2_buffer b{}; v4l2_plane p[VIDEO_MAX_PLANES]{};
            while(out.dequeue(b,p)) {
                require(p[0].data_offset<=p[0].bytesused && p[0].bytesused<=out.buffers[b.index][0].size,"capture length invalid");
                unsigned size=p[0].bytesused-p[0].data_offset;
                OwnedPacket packet;packet.ptsUs=b.timestamp.tv_sec*1000000LL+b.timestamp.tv_usec;packet.flags=b.flags;packet.sequence=b.sequence;
                auto* begin=static_cast<uint8_t*>(out.buffers[b.index][0].ptr)+p[0].data_offset;
                packet.bytes.assign(begin,begin+size); // owned copy before callback/requeue
                stream.write(reinterpret_cast<const char*>(packet.bytes.data()),packet.bytes.size()); require(bool(stream),"stream write failed"); total+=size;
                consumer(std::move(packet));
                log<<"{\"event\":\"capture\",\"sequence\":"<<b.sequence<<",\"pts_us\":"<<b.timestamp.tv_sec*1000000LL+b.timestamp.tv_usec<<",\"bytes\":"<<size<<",\"flags\":"<<b.flags<<"}"<<std::endl;
                moved=true; last=b.flags&V4L2_BUF_FLAG_LAST;
                if(last) break;
                out.queue(b.index,{0});
                memset(p,0,sizeof(p));
            }
        }
        v4l2_buffer b{}; v4l2_plane p[VIDEO_MAX_PLANES]{};
        while(returned<queued && in.dequeue(b,p)) {
            ++returned; moved=true;
            log<<"{\"event\":\"input_returned\",\"index\":"<<b.index<<",\"count\":"<<returned<<"}"<<std::endl;
            if(queued<options.frameCount) submit(b.index);
            memset(p,0,sizeof(p));
        }
        if(queued==options.frameCount && !draining) {
            v4l2_encoder_cmd c{}; c.cmd=V4L2_ENC_CMD_STOP; checked(d.fd,VIDIOC_ENCODER_CMD,&c,"ENCODER_CMD STOP");
            draining=true; log<<"{\"event\":\"drain_started\"}"<<std::endl;
        }
        // Caller inference/model initialization may be slow while VPU waits for
        // a new input. Keep codec deadlines unchanged on a separately labelled
        // clock excluding bounded producer calls; outer runner remains180s.
        auto now=std::chrono::steady_clock::now()-producerPaused;
        if(moved) progress=now;
        require(now-began<std::chrono::seconds(25),"codec elapsed excluding producer exceeded25s");
        require(now-progress<std::chrono::seconds(5),"encoder stalled");
        if(!moved) {
            pollfd pfd{d.fd,POLLIN|POLLOUT|POLLPRI,0}; int r=poll(&pfd,1,20);
            if(r<0 || (pfd.revents&(POLLERR|POLLHUP|POLLNVAL))) {
                log<<"{\"event\":\"poll_error\",\"return\":"<<r<<",\"revents\":"<<pfd.revents<<",\"errno\":"<<(r<0 ? errno:0)<<",\"queued\":"<<queued<<",\"returned\":"<<returned<<"}"<<std::endl;
            }
            require(r>=0 || errno==EINTR,"poll failed"); require(!(pfd.revents&(POLLERR|POLLHUP|POLLNVAL)),"poll device failure");
        }
    }
    require(queued==options.frameCount && returned==options.frameCount && last && total>0,"incomplete stream");
    in.stop(); out.stop(); stream.close();submitted.close();require(bool(stream) && bool(submitted),"stream finalization failed");
    log<<"{\"event\":\"encoding_complete\",\"queued\":"<<queued<<",\"returned\":"<<returned<<",\"last\":true,\"bytes\":"<<total<<",\"producer_paused_ns\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(producerPaused).count()<<",\"hdmi\":false,\"npu_owned_by_caller\":true}"<<std::endl;
    return {queued,returned,total,last};
}
}
