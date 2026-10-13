"""Apply the approved internal orchestration extraction after source migration."""
from pathlib import Path
import re
from core_refactor_format import TOKEN, format_cpp

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'software/demo/board'


def brace_end(source, start):
    depth = 0
    for match in TOKEN.finditer(source, start):
        if match.lastgroup in ('literal', 'comment', 'directive'):
            continue
        if match.group() == '{':
            depth += 1
        elif match.group() == '}':
            depth -= 1
            if depth == 0:
                return match.end()
    raise ValueError('Unbalanced extraction')


def main():
    path = BOARD / 'main.cpp'
    source = path.read_text(encoding='utf-8')
    first = source.index('        std::map')
    last = source.index('        out = options.at("--output");', first)
    source = source[:first] + '''        // 1. 参数解析独立于设备初始化，所有默认值和拒绝规则保持。
        const auto options = wifi_demo::parseOptions(argc, argv);
        const auto maximum = options.maximum;
        const auto port = options.input_port;
        const auto rtsp = options.rtsp_port;
''' + source[last:]
    source = source.replace('#include <map>', '#include "demo_options.hpp"')
    source = source.replace('out = options.at("--output");', 'out = options.output;')
    source = source.replace('options.at("--model-dir")', 'options.model')
    source = source.replace('get("--bind", "192.168.126.49")', 'options.bind')
    for prefix, comment in (
        ('        const auto began = now();', '2. 子进程先启动，主线程随后创建Engine；设备描述符不传给显示子进程。'),
        ('        while (results.size() < maximum)', '3. 消费完整拥有值窗口，先保存原结果，再发布视频姿态。'),
        ('    if (video) {', '4. 先结束视频工作线程，再释放输入、视频和显示对象。'),
        ('    if (!out.empty() && fs::is_directory(out)) {', '5. 保存全部已拥有结果和诊断；保存失败不覆盖更早的原错误。'),
        ('    engine.reset();', '6. 所有工作线程已join，最后释放主线程Engine。'),
    ):
        source = source.replace(prefix, '    ' * (2 if prefix.startswith('        ') else 1) + '// ' + comment + '\n' + prefix, 1)
    path.write_text(source, encoding='utf-8', newline='\n')

    # Each thread still starts in the same constructor order. Helpers run only
    # in that thread, retain the original try/catch and access the same members.
    original = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1/original-demo/board/demo_video.cpp'
    source = original.read_text(encoding='utf-8')
    helpers = []
    for marker, method, signature, call in (
        ('network=std::thread([this,port]', 'runNetwork', 'unsigned port', 'port'),
        ('renderer=std::thread([this]', 'runRenderer', '', ''),
        ('encoder=std::thread([this,warm=std::move(warm)]', 'runEncoder', 'const pose::video::OwnedFrame& warm', 'warm'),
    ):
        start = source.index(marker) + len(marker)
        end = brace_end(source, start)
        body = source[start + 1:end - 1]
        source = source[:start] + '{' + method + '(' + call + ');}' + source[end:]
        helpers.append('void ' + method + '(' + signature + ') {' + body + '}\n')
    position = source.index('    void fail(')
    source = source[:position] + '\n// 各线程入口独立封装，保留原局部变量生命周期与错误传播。\n' + '\n'.join(helpers) + source[position:]
    source = '// 视频编排：绘图、VPU和网络各自拥有线程；join顺序与原现场证据契约保持。\n\n' + format_cpp(source)
    (BOARD / 'demo_video.cpp').write_text(source, encoding='utf-8', newline='\n')

    cmake = ROOT / 'software/demo/CMakeLists.txt'
    text = cmake.read_text(encoding='utf-8').replace('board/main.cpp board/demo_video.cpp', 'board/main.cpp board/demo_options.cpp board/demo_video.cpp')
    cmake.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
