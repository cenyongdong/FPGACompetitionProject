"""从已验收三窗归档取实际CSI，绑定旧参考和模型；仅本机打包，不部署。"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import struct
import tarfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1'
NAMES = ('S11_01_308', 'S11_01_309', 'S11_01_310')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def package(source, build, model, output):
    manifest = load(source / 'source-manifest.json')
    compiled = load(build / 'build-result.json')
    if compiled['status'] != 'compiled_not_board_executed' or compiled['source_manifest_sha256'] != sha(source / 'source-manifest.json'):
        raise ValueError('Compiled source identity differs')
    if sha(build / 'pose_engine_timing') != compiled['binary_sha256']:
        raise ValueError('Binary identity differs')
    for relative, digest in manifest['files'].items():
        if sha(source / relative) != digest:
            raise ValueError('Source package identity differs: ' + relative)
    for name, key in (('piw24_ZG.json', 'graph_sha256'), ('piw24_ZG.raw', 'raw_sha256')):
        if sha(model / name) != manifest[key]:
            raise ValueError('Model identity differs: ' + name)
    review_path = EVIDENCE / 'board/short.review.json'
    review = load(review_path)
    archive = EVIDENCE / 'board/return-short.tar'
    if review['status'] != 'end_to_end_demo_passed' or review['fixed_reference_bitwise_cases'] != list(NAMES):
        raise ValueError('Accepted three-window reference differs')
    if sha(archive) != review['board_archive_sha256']:
        raise ValueError('Original accepted archive changed')
    recovery = load(EVIDENCE / 'recovered-inputs.json')['copied_files']['reference']
    # 只从归档读取已知普通文件字节，不解包链接、路径或权限。
    fixtures = {}
    with tarfile.open(archive, 'r:*') as tar:
        members = tar.getmembers()
        def data(suffix):
            found = [m for m in members if m.name.endswith(suffix)]
            if len(found) != 1 or not found[0].isfile():
                raise ValueError('Ambiguous/non-file accepted archive member: ' + suffix)
            if found[0].size > 1024 * 1024:
                raise ValueError('Accepted fixture too large')
            with tar.extractfile(found[0]) as stream:
                return stream.read()
        before_log = data('/before.dmesg.txt').decode(errors='replace')
        linux = re.search(r'Linux version [^\r\n]+', before_log)
        if not linux:
            raise ValueError('Archived kernel version missing; resolve identity before board work')
        expected_preflight = json.loads(data('/preflight.json'))
        for i, name in enumerate(NAMES):
            suffix = '/results/results/frame-' + str(1000000 + i) + '/'
            payload = data(suffix + 'csi.payload')
            if len(payload) != 86400:
                raise ValueError('Accepted CSI payload length differs')
            fixtures[name + '.csi'] = struct.pack('<8sIIQQ', b'PIWCSI1\0', 1, 86400, 1000000 + i, 0) + payload
            for kind in ('input', 'scores', 'poses'):
                blob = data(suffix + kind + '.f32')
                relative = ('reference/' if kind == 'input' else 'r6-reference/') + name + '.' + kind + '.f32'
                if hashlib.sha256(blob).hexdigest() != recovery[relative]:
                    raise ValueError('Actual accepted output differs from frozen reference: ' + relative)
                fixtures[name + '.' + kind + '.f32'] = blob
    if output.exists():
        raise FileExistsError('Preserve prior delivery package')
    output.mkdir(parents=True)
    (output / 'models').mkdir()
    (output / 'fixtures').mkdir()
    for name in ('piw24_ZG.json', 'piw24_ZG.raw'):
        shutil.copyfile(model / name, output / 'models' / name)
    for name, blob in fixtures.items():
        (output / 'fixtures' / name).write_bytes(blob)
    shutil.copyfile(build / 'pose_engine_timing', output / 'pose_engine_timing')
    for name in ('board_run.py', 'analyze.py'):
        shutil.copyfile(source / name, output / name)
    shutil.copyfile(ROOT / 'tools/pose-v1/board_application_preflight.py', output / 'board_application_preflight.py')
    shutil.copyfile(build / 'build-result.json', output / 'build-result.json')
    shutil.copyfile(source / 'source-manifest.json', output / 'source-manifest.json')
    delivery = {'status': 'delivery_prepared_not_deployed', 'binary_sha256': compiled['binary_sha256'],
                'source_manifest_sha256': sha(source / 'source-manifest.json'),
                'reference_archive_sha256': sha(archive), 'reference_review_sha256': sha(review_path),
                'expected_linux_version': linux.group(0).strip(),
                'expected_boot_files': expected_preflight['boot_files'],
                'libraries': compiled['libraries'], 'sdk_headers_normalized_sha256': manifest['sdk_headers_normalized_sha256'],
                'files': {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output / 'package.json').write_text(json.dumps(delivery, indent=2) + '\n')
    return delivery


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.source.resolve(), args.build.resolve(), args.model_dir.resolve(), args.output.resolve())
    print('Delivery prepared; no board execution:', args.output)
