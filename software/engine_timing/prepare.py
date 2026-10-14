"""导出锁定核心的隔离诊断副本；精确锚点不符即停止，不修改正式源码。"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def replace(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Diagnostic patch anchor changed: ' + before[:90])
    return text.replace(before, after)


def adapt_engine(text):
    text = replace(text, '#include "application_core.hpp"',
                   '#include "application_core.hpp"\n#include "sdk_profile.hpp"')
    text = replace(text, 'Clock::time_point operation_start;',
                   'Clock::time_point operation_start;\n        fc::Sample operation_sample;')
    text = replace(text, 'const auto begin = Clock::now();',
                   'fc::begin_initialization();\n            fc::Span initialization("init.total");\n            const auto begin = Clock::now();')
    for line, kind in (
        ('graph = xir::Network::CreateFromJsonFile(c.graph.string());', 'init.parse'),
        ('graph.lazyLoadParamsFromFile(c.raw.string());', 'init.load_parameters'),
        ('parameters(graph, c.evidence);', 'init.parameter_audit_io'),
        ('device = open_device(c.evidence);', 'init.open_device'),
        ('session = Session::Create<zg330::ZG330Backend, HostBackend>(graph.view(), { device, HostDevice::Default() });', 'init.session_create'),
        ('session.apply();', 'init.session_apply'),
    ):
        text = replace(text, line, '{ fc::Span sample("' + kind + '"); ' + line + ' }')
    text = replace(text, 'session.enableTimeProfile(false);',
                   'session.enableTimeProfile(pose_v1::timing_sdk::enabled);')
    text = replace(text, 'operation_start = Clock::now();',
                   'operation_sample = fc::sample();\n                operation_start = operation_sample.wall;')
    text = replace(text, 'const auto operation_end = Clock::now();',
                   'const auto operation_sample_end = fc::sample();\n                const auto operation_end = operation_sample_end.wall;')
    text = replace(text, 'operation_start, operation_end);',
                   'operation_start, operation_end, operation_sample, operation_sample_end);')
    # SDK采集从公开适配入口调用，避开process_window内的runtime.total。
    text = replace(text, 'double Engine::init_ms() const {',
                   'void Engine::collect_timing_profile() {\n        fc::check();\n        pose_v1::timing_sdk::collect(impl_->session, impl_->device, impl_->frame, impl_->invocation);\n    }\n\n    double Engine::init_ms() const {')
    before = '"{\\\"enabled\\\":false,\\\"wall_clock\\\":\\\"std::chrono::steady_clock\\\",\\\"unit\\\":\\\"ns\\\"}\\n"'
    after = 'std::string("{\\\"enabled\\\":") + (pose_v1::timing_sdk::enabled ? "true" : "false") + ",\\\"wall_clock\\\":\\\"std::chrono::steady_clock\\\",\\\"unit\\\":\\\"ns\\\"}\\n"'
    return replace(text, before, after)


def adapt_bridge(text):
    for label, variable, kind in (('auto allocate = Clock::now();', 'allocation_sample', 'bridge.allocate'),
                                  ('auto compute = Clock::now();', 'compute_sample', 'bridge.cpu')):
        original = 'allocate' if kind == 'bridge.allocate' else 'compute'
        text = replace(text, label, f'const auto {variable} = forward_clock::sample();')
        old = f'forward_clock::record("{kind}", op->op_id, ' + ('index' if original == 'allocate' else '0') + f', {original}, Clock::now());'
        new = f'forward_clock::record("{kind}", op->op_id, ' + ('index' if original == 'allocate' else '0') + f', {variable}, forward_clock::sample());'
        text = replace(text, old, new)
    # 保留已有582计数检查，仅给原区间增加观测，不增加poll或同步。
    text = replace(text, 'auto result = pose::stage_observation::waitFresh(',
                   'forward_clock::Span counter_span("bridge.counter_wait", op->op_id, index);\n                    auto result = pose::stage_observation::waitFresh(')
    text = replace(text, 'forward_clock::Span t("bridge.copy", op->op_id, index);',
                   'forward_clock::transfer("bridge.copy", op->op_id, index, value.tensorType().bytes(), host(src) ? "host_to_host" : "device_to_host");\n                forward_clock::Span t("bridge.copy", op->op_id, index);')
    text = replace(text, 'forward_clock::Span t("bridge.writeback", op->op_id, i);',
                   'forward_clock::transfer("bridge.writeback", op->op_id, i, computed[i].dtype().bytes(), host(target) ? "host_to_host" : "host_to_device");\n                forward_clock::Span t("bridge.writeback", op->op_id, i);')
    return text


def prepare(output):
    lock_path = ROOT / 'software/demo/baseline-lock.json'
    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    aliases = {}
    for relative, item in lock['build_files'].items():
        if sha(ROOT / relative) != item['sha256']:
            raise ValueError('Baseline identity changed: ' + relative)
        alias = item['destination']
        if Path(alias).name != alias or alias in aliases:
            raise ValueError('Invalid/duplicate baseline alias: ' + alias)
        aliases[alias] = ROOT / relative
    # 先验证锚点，再创建新目录；失败目录也不能覆盖重用。
    engine = adapt_engine(aliases['application_core.cpp'].read_text(encoding='utf-8'))
    bridge = adapt_bridge(aliases['read_input_bridge.cpp'].read_text(encoding='utf-8'))
    header = replace(aliases['application_core.hpp'].read_text(encoding='utf-8'),
                     'void save_evidence();', 'void save_evidence();\n        void collect_timing_profile();')
    if output.exists():
        raise FileExistsError('Preserve previous diagnostic package: ' + str(output))
    output.mkdir(parents=True)
    baseline = output / 'baseline'
    baseline.mkdir()
    for name, source in aliases.items():
        shutil.copyfile(source, baseline / name)
    before = {name: sha(baseline / name) for name in aliases}
    for name, content in {'application_core.cpp': engine, 'read_input_bridge.cpp': bridge,
                          'application_core.hpp': header}.items():
        (baseline / name).write_text(content, encoding='utf-8', newline='\n')
    shutil.copyfile(HERE / 'application_clock.hpp', baseline / 'application_clock.hpp')
    shutil.copyfile(HERE / 'sdk_profile.hpp', baseline / 'sdk_profile.hpp')
    for name in ('main.cpp', 'CMakeLists.txt', 'analyze.py', 'board_run.py', 'make_package.py'):
        shutil.copyfile(HERE / name, output / name)
    manifest = {
        'status': 'source_prepared_not_compiled_or_board_executed',
        'baseline_lock_sha256': sha(lock_path),
        'original_sources': lock['build_files'],
        'changes': {name: {'before': before.get(name), 'after': sha(baseline / name)}
                    for name in ('application_core.cpp', 'application_core.hpp', 'read_input_bridge.cpp', 'application_clock.hpp')},
        'graph_sha256': lock['graph_sha256'], 'raw_sha256': lock['raw_sha256'],
        'sdk_headers_normalized_sha256': lock['sdk_headers_normalized_sha256'],
        'host_library_sha256': lock['host_library_sha256'], 'zg_library_sha256': lock['zg_library_sha256'],
        'device_protocol': 'axi://zg330aiu?npu=0x40000000&dma=0x80000000',
        'old_DATA_investigation_resumed': False,
        'files': {path.relative_to(output).as_posix(): sha(path)
                  for path in sorted(output.rglob('*')) if path.is_file()},
    }
    (output / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())
    print('Prepared isolated timing sources:', args.output)
