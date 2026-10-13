"""Create the approved formal core and record the original source identities."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from core_refactor_format import format_cpp, format_python, tokens

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1'
CORE = ROOT / 'software/core'
DEMO = ROOT / 'software/demo'

GROUPS = {
    'input': 'preprocess tcp_receiver',
    'inference': 'application_core read_input_bridge input_read_sdk input_read_contract host_cpu_adapter lazy_runtime_validation mixed_bridge mixed_fusion_baseline',
    'diagnostics': 'host_failure_evidence failure_source_readback host_stage_observation invocation_evidence producer_count_observation tensor_identity_observation application_clock content_diagnostic bounded_load_contract',
    'display': 'display_process display_protocol display_queue display_worker skeleton_render',
    'video': 'timed_resident_encoder resident_frame_queue vpu_resident_encoder vpu_pipeline_encoder vpu_encoder video_frame_marker',
    'stream': 'h264_access_unit access_unit_channel timed_guarded_rtsp guarded_rtsp online_rtsp',
}
DESCRIPTIONS = {
    'input': '输入模块：固定CSI契约、完整记录重组及训练等价预处理；窗口按拥有值交接。',
    'inference': '推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。',
    'diagnostics': '诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。',
    'display': '显示模块：SDK无关的子进程、IPC和像素处理；传递完整拥有值。',
    'video': '视频模块：有界NV12及V4L2编码；缓冲所有权、正常drain与异常回收保持。',
    'stream': '流媒体模块：拥有H264访问单元、有界通道和RTSP；网络对象仅由事件线程操作。',
}
FUNCTION_COMMENTS = {
    'preprocess': {
        'Tokens preprocess(': '1. 按固定训练顺序生成幅度和校正相位；保留浮点运算与signed-zero行为。',
        'Window read_window(': '2. 读取完整PIWCSI1记录，先验证头部与长度，再恢复原始复数窗口。',
        'void write_tokens(': '3. 保存实际FP32输入，不执行模型推理。',
    },
    'application_core': {
        'explicit Impl(': '1. 校验身份并注册Host算子；创建、apply及安装回调的顺序不变。',
        'Result process(': '2. 串行处理完整窗口；异常永久停止本Engine，不重建或重试。',
        'void save(': '3. 在计量路径之外保存本次真实执行证据。',
    },
    'read_input_bridge': {
        'void register_ops(': '1. 仅注册当前图缺失的算子；原Gather注册必须保持。',
        'std::vector<xrt::Tensor> forward(': '2. 校验并等待输入，公开SDK搬入Host，执行CPU核，再写回输出。',
    },
    'host_cpu_adapter': {
        'void validate_spec(': '1. 验证固定FP32形状、轴和全有效分布，拒绝未批准规格。',
        'void register_missing(': '2. 显式注册缺失CPU算子；不覆盖已有或部分注册。',
        'std::vector<xrt::Tensor> forward(': '3. 用临时稠密描述调用SDK数学核；不修改图及原始布局。',
    },
    'tcp_receiver': {
        'Window decode_record(': '1. 校验完整记录并恢复拥有值；TCP分包边界不代表记录边界。',
        'Read exact(': '2. 有界重组所需字节；中断记录、闲置超时和停止分别处理。',
        'void loop(': '3. 接收线程只发布完整窗口，消费中的窗口不受槽覆盖影响。',
        'void stop(': '4. 唤醒阻塞操作；worker结束后才释放描述符。',
    },
    'failure_source_readback': {
        'void capture(': '失败后只读取证：先校验存储身份并拥有全部目标缓冲，再连续执行两轮SDK read。',
    },
    'timed_resident_encoder': {
        'void allocate(': '1. 保留协商出的两缓冲和QUERYBUF不透明cookie；不猜测物理地址。',
        'void queue(': '2. 仅CPU拥有的输入缓冲可以写入和提交；成功QBUF后归驱动拥有。',
        'bool dequeue(': '3. DQBUF成功后才归还缓冲所有权，异常原样停止。',
        'EncodeResult encodeResident(': '4. 固定格式协商、采样、编码和drain；所有预算与日志契约保持。',
    },
    'timed_guarded_rtsp': {
        'void serveGuardedAccessUnits(': '事件线程持有live555对象；失败先停止事件循环，再按原顺序回收。',
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotate(text, filename, group):
    for prefix, comment in FUNCTION_COMMENTS.get(filename, {}).items():
        pattern = r'(?m)^( *)(?=' + re.escape(prefix) + ')'
        text = re.sub(pattern, lambda m: m[1] + '// ' + comment + '\n' + m[1], text)
    return '// ' + DESCRIPTIONS[group] + '\n// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。\n\n' + text


def main():
    assert not (EVIDENCE / 'source-migration.json').exists(), 'Preserve completed migration'
    lock = json.loads((DEMO / 'baseline-lock.json').read_text(encoding='utf-8'))
    for rel, item in lock['build_files'].items():
        assert sha(ROOT / rel) == item['sha256'], 'Source identity changed: ' + rel
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    snapshot = EVIDENCE / 'original-demo'
    if not snapshot.exists():
        shutil.copytree(DEMO, snapshot, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copyfile(DEMO / 'baseline-lock.json', EVIDENCE / 'baseline-lock.before.json')
    else:
        assert (EVIDENCE / 'baseline-lock.before.json').read_bytes() == (DEMO / 'baseline-lock.json').read_bytes()
    # Freeze every historical source identity, including all original tests.
    original_files = {p.relative_to(ROOT).as_posix(): sha(p)
                      for folder in ('software/pose_v1', 'tools/pose-v1')
                      for p in (ROOT / folder).rglob('*')
                      if p.is_file() and p.suffix in ('.cpp', '.hpp', '.h', '.py', '.ps1', '.sh')
                      and 'evidence' not in p.parts and '__pycache__' not in p.parts}
    (EVIDENCE / 'frozen-sources.before.json').write_text(json.dumps(original_files, indent=2) + '\n', encoding='utf-8')
    by_destination = {item['destination']: (rel, item) for rel, item in lock['build_files'].items()}
    cmake = (DEMO / 'CMakeLists.txt').read_text(encoding='utf-8')
    pending = re.findall(r'\$\{BASELINE_DIR\}/([\w.]+)', cmake)
    for path in (DEMO / 'board').glob('*'):
        if path.suffix in ('.cpp', '.hpp'):
            pending += re.findall(r'#include\s+"([^"]+)"', path.read_text(encoding='utf-8'))
    visited = set()
    group_for = {name: group for group, names in GROUPS.items() for name in names.split()}
    mapping = []
    new_lock = dict(lock)
    new_lock['build_files'] = dict(lock['build_files'])
    while pending:
        name = pending.pop(0)
        if name in visited or name not in by_destination:
            continue
        visited.add(name)
        rel, item = by_destination[name]
        source = (ROOT / rel).read_text(encoding='utf-8')
        pending += re.findall(r'#include\s+"([^"]+)"', source)
        if name == 'tcp_transport_check.cpp':
            continue  # Existing test content stays in its frozen original location.
        group = group_for[Path(name).stem]
        destination = CORE / group / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        formatted = annotate(format_cpp(source), Path(name).stem, group)
        assert tokens(source) == tokens(formatted), name
        destination.write_text(formatted, encoding='utf-8', newline='\n')
        new_rel = destination.relative_to(ROOT).as_posix()
        del new_lock['build_files'][rel]
        new_lock['build_files'][new_rel] = dict(item, sha256=sha(destination))
        mapping.append({'original': rel, 'destination': new_rel, 'build_alias': name,
                        'original_sha256': item['sha256'], 'new_sha256': sha(destination),
                        'cpp_tokens_identical': True})
    # Current board code keeps its public names; only the source presentation changes here.
    for path in (DEMO / 'board').glob('*'):
        if path.suffix not in ('.cpp', '.hpp'):
            continue
        old = path.read_text(encoding='utf-8')
        description = {
            'main': '应用入口：主线程持有Engine；按原顺序启动、消费窗口、保存现场及回收资源。',
            'demo_engine': '推理适配：集中配置既有诊断模块，向应用暴露最小推理及保存接口。',
            'demo_video': '视频编排：绘图、VPU及网络分别拥有工作线程；finish后全部join。',
            'demo_results': '结果保存：拥有原始窗口和全部模型输出；写入新目录，不覆盖原值。',
        }[path.stem]
        path.write_text('// ' + description + '\n\n' + format_cpp(old), encoding='utf-8', newline='\n')
    python_files = [DEMO / n for n in ('build.py', 'deploy.py', 'board/runner.py', 'host/run.py', 'host/replay.py', 'host/viewer.py')]
    for path in python_files:
        old = path.read_text(encoding='utf-8')
        result = format_python(old)
        result = re.sub(r'(?m)^(def \w+\()', r'\n\n# 独立逻辑步骤：保持原输入、预算、错误传播及产物契约。\n\1', result)
        result = re.sub(r'(?m)^(if __name__ ==)', r'\n\n\1', result)
        path.write_text(result, encoding='utf-8', newline='\n')
    source = ROOT / 'tools/pose-v1/csi_io.py'
    destination = CORE / 'input/csi_io.py'
    destination.write_text('# CSI公共输入契约：只读取原始复数与编码，不做模型预处理。\n' + format_python(source.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    mapping.append({'original': source.relative_to(ROOT).as_posix(), 'destination': destination.relative_to(ROOT).as_posix(),
                    'original_sha256': sha(source), 'new_sha256': sha(destination), 'python_ast_identical': True})
    replay = DEMO / 'host/replay.py'
    text = replay.read_text(encoding='utf-8').replace("ROOT / 'tools/pose-v1'", "ROOT / 'software/core/input'")
    replay.write_text(text, encoding='utf-8', newline='\n')
    new_lock['prior_baseline'] = lock['prior_baseline'] + '; explicit formal-core migration 2026-10-13'
    new_lock['source_migration'] = 'tools/pose-v1/evidence/core-refactor-20261013-r1/source-migration.json'
    (DEMO / 'baseline-lock.json').write_text(json.dumps(new_lock, indent=2) + '\n', encoding='utf-8', newline='\n')
    (EVIDENCE / 'source-migration.json').write_text(json.dumps({'status': 'source_migrated_not_yet_compiled', 'files': mapping}, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Migrated', len(mapping), 'production source files; frozen original files:', len(original_files))


if __name__ == '__main__':
    main()
