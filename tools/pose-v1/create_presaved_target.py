"""Save owned returned values before the unchanged oracle; preserve r1 sources."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];src=root/'software/pose_v1'
header=(src/'include/failed_result_evidence.hpp').read_text(encoding='utf-8').replace('saveOrCaptureFailedResult','saveThenVerifyResult')
header=header.replace('// Diagnostic adapter only: preserve the first rejected result, then rethrow.','// Diagnostic adapter only: persist every owned result before the strict gate.')
(src/'include/presaved_result_evidence.hpp').write_bytes(header.encode())
old=(src/'src/failed_result_evidence.cpp').read_text(encoding='utf-8')
prefix=old[:old.index('void saveOrCaptureFailedResult')].replace('failed_result_evidence.hpp','presaved_result_evidence.hpp')
body='''void saveThenVerifyResult(const FixtureWindow& c,const pose_v1::application::Result& r,
                          const pose_v1::Window& actual,size_t call,const std::filesystem::path& out,
                          std::ofstream& calls){
    const auto parent=out/"presaved-results";
    if(!std::filesystem::exists(parent))std::filesystem::create_directory(parent);
    const auto directory=parent/std::to_string(call);
    if(std::filesystem::exists(directory))throw std::runtime_error("Preserve presaved result");
    std::filesystem::create_directory(directory);
    persistBytes(directory/"input.f32",r.input.data(),sizeof(r.input));
    persistBytes(directory/"scores.f32",r.scores.data(),sizeof(r.scores));
    persistBytes(directory/"poses.f32",r.poses.data(),sizeof(r.poses));
    persistBytes(directory/"raw-payload.bin",actual.csi.data(),sizeof(actual.csi));
    std::ofstream f(directory/"identity.json");f<<std::setprecision(17);
    f<<"{\\\"saved_before_gate\\\":true,\\\"case\\\":\\\""<<c.name<<"\\\",\\\"call\\\":"<<call<<",\\\"frame_id\\\":"<<r.frame_id<<",\\\"invocation\\\":"<<r.invocation
     <<",\\\"before_clear\\\":"<<r.before_clear<<",\\\"before_forward\\\":"<<r.before_forward<<",\\\"completed_layers\\\":"<<r.completed_layers
     <<",\\\"host_callbacks\\\":"<<r.host_callbacks<<",\\\"zg_callbacks\\\":"<<r.zg_callbacks<<",\\\"input\\\":";
    difference(f,r.input,c.input);f<<",\\\"scores\\\":";difference(f,r.scores,c.scores);f<<",\\\"poses\\\":";difference(f,r.poses,c.poses);f<<"}\\n";
    f.close();if(!f)throw std::runtime_error("Presaved result metadata write failed");
    // Same gate, exception and successful result files as the frozen adapter.
    saveVerifiedResult(c,r,call,out,calls);
}
}
'''
(src/'src/presaved_result_evidence.cpp').write_bytes((prefix+body).encode())
entry=(src/'src/live_tcp_evidence_check.cpp').read_text(encoding='utf-8').replace('failed_result_evidence.hpp','presaved_result_evidence.hpp').replace('saveOrCaptureFailedResult','saveThenVerifyResult')
(src/'src/live_tcp_presaved_check.cpp').write_bytes(entry.encode())
test=(src/'src/failed_result_selftest.cpp').read_text(encoding='utf-8').replace('failed_result_evidence.hpp','presaved_result_evidence.hpp').replace('saveOrCaptureFailedResult','saveThenVerifyResult')
test=test.replace('std::filesystem::exists(out/"failed-result")!=(i!=0)','!std::filesystem::exists(out/"presaved-results/0")')
test=test.replace('if(i&&std::filesystem::file_size(out/"failed-result/scores.f32")!=400)','if(std::filesystem::file_size(out/"presaved-results/0/scores.f32")!=400)')
test=test.replace('\\\"failure_preserved\\\":2,','\\\"failure_preserved\\\":2,\\\"all_presaved\\\":3,')
(src/'src/presaved_result_selftest.cpp').write_bytes(test.encode())
cmake=(root/'tools/pose-v1/tcp-evidence-CMakeLists.txt').read_text(encoding='utf-8').replace('live_tcp_evidence_check.cpp','live_tcp_presaved_check.cpp').replace('failed_result_evidence.cpp','presaved_result_evidence.cpp').replace('failed_result_selftest.cpp','presaved_result_selftest.cpp')
(root/'tools/pose-v1/tcp-presaved-CMakeLists.txt').write_bytes(cmake.encode())
builder=(root/'tools/pose-v1/Build-TcpEvidence.ps1').read_text(encoding='utf-8').replace('mixed-20261008-tcp-evidence-r1','mixed-20261008-tcp-presaved-r1')
(root/'tools/pose-v1/Build-TcpPresaved.ps1').write_bytes(builder.encode())
