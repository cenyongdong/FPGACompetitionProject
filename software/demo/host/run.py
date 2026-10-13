"""Directory replay + real-time viewer. Start the bounded board server first."""
from pathlib import Path
import argparse, json, subprocess, sys
from replay import DEFAULT_DATA, prepare, send


# 编排输入准备、播放器启动和发送；finally只回收本批拥有的播放器。
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=DEFAULT_DATA)
    p.add_argument('--board', default='192.168.126.49')
    p.add_argument('--input-port', type=int, default=39001)
    p.add_argument('--rtsp-port', type=int, default=8554)
    p.add_argument('--frames', type=int, default=60)
    p.add_argument('--hz', type=float, default=2)
    p.add_argument('--sequence', default='')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--headless', action='store_true')
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--viewer-python', type=Path, default=Path.home() / 'miniconda3/envs/WIFI-densepose/python.exe')
    a = p.parse_args()
    assert not a.output.exists()
    a.output.mkdir()
    assert 1 <= a.frames <= 100 and 0.5 <= a.hz <= 2 and (a.frames / a.hz <= 55)
    catalog, payloads = prepare(a.data, a.output / 'inputs', a.frames, a.sequence)
    if a.prepare_only:
        print('Prepared', len(catalog), 'raw CSI windows; no network/inference')
        return
    assert a.viewer_python.is_file()
    assert 1024 <= a.input_port <= 65535 and 1024 <= a.rtsp_port <= 65535
    url = f'rtsp://{a.board}:{a.rtsp_port}/pose'
    args = [str(a.viewer_python), str(Path(__file__).with_name('viewer.py')), '--url',
        url, '--output', str(a.output)]
    if a.headless:
        args.append('--headless')
    viewer = None
    try:
        with (a.output / 'viewer.stdout.txt').open('wb') as stdout, (a.output / 'viewer.stderr.txt').open('wb') as stderr:
            viewer = subprocess.Popen(args, stdout=stdout, stderr=stderr, creationflags=getattr(subprocess,
                'CREATE_NO_WINDOW', 0))
            (a.output / 'viewer.pid').write_text(str(viewer.pid) + '\n')
            sent = send(a.board, a.input_port, a.hz, catalog, payloads, a.output, viewer)
            code = viewer.wait(timeout=15)
            if code:
                raise RuntimeError('Viewer failed; inspect viewer.json/stderr')
        (a.output / 'host-summary.json').write_text(json.dumps({'status': 'CSI_sent_actual_RTSP_decoded',
            'sent': len(sent), 'url': url, 'GUI': not a.headless, 'raw_preprocessing_on_host': False,
            'board_success_requires_return_review': True}, indent=2) + '\n', encoding='utf-8')
        print('Sent', len(sent), 'CSI windows; actual board RTSP displayed:', url)
    finally:
        if viewer and viewer.poll() is None:
            viewer.terminate()
            viewer.wait(timeout=5)


if __name__ == '__main__':
    main()
