"""One-time extraction from frozen r4 into isolated finite encoder API."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
original=ROOT/'software/pose_v1/src/vpu_encode_check.cpp'
saved=ROOT/'.local/pose-v1-build/vpu-20261007-r4/vpu_encode_check.cpp'
assert original.read_bytes()==saved.read_bytes(),'Frozen r4 source changed'
s=original.read_text()
s=s[:s.index('int main(int argc')]
s=s.replace('#include <linux/videodev2.h>','#include "vpu_encoder.hpp"\n#include <linux/videodev2.h>')
s=s.replace('FPS=10, FRAMES=30','FPS=10')
old='void run(bool encode,const std::filesystem::path& input,const std::filesystem::path& dest) {'
new='''}
namespace pose::video {
EncodeResult encodeNv12File(const std::filesystem::path& input,const std::filesystem::path& dest,const EncodeOptions& options,bool encode) {
    require(options.allowVpuStream,"explicit VPU authorization required");
    require(options.frameCount>=2 && options.frameCount<=60,"frame count outside2..60");
    require(std::filesystem::file_size(input)==size_t(W)*H*3/2*options.frameCount,"input size differs before device access");'''
assert s.count(old)==1
s=s.replace(old,new).replace('FRAMES','options.frameCount')
s=s.replace('return; }','return {}; }')
s=s.replace('    require(std::filesystem::file_size(input)==size_t(W)*H*3/2*options.frameCount,"input size differs");\n','')
offset=s.index('    log<<"{\\"event\\":\\"encoding_complete')
s=s[:offset]+s[offset:].replace('\n}\n}','\n    return {queued,returned,total,last};\n}\n}',1)
p=ROOT/'software/pose_v1/src/vpu_encoder.cpp'
assert not p.exists(),'Preserve existing candidate'
p.write_bytes(s.encode())
print('Isolated API generated; original unchanged')
