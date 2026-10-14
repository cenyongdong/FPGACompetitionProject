"""闭合开发交付身份及实际验证范围，不把编译/合成测试记作板测。"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    lock = load(ROOT / 'software/demo/baseline-lock.json')
    for relative, item in lock['build_files'].items():
        if sha(ROOT / relative) != item['sha256']:
            raise ValueError('Formal core changed: ' + relative)
    source = load(args.source / 'source-manifest.json')
    for relative, expected in source['files'].items():
        if sha(args.source / relative) != expected:
            raise ValueError('Prepared source changed: ' + relative)
    build = load(args.build / 'build-result.json')
    package = load(args.package / 'package.json')
    if build['source_manifest_sha256'] != sha(args.source / 'source-manifest.json'):
        raise ValueError('Build/source binding differs')
    if sha(args.build / 'pose_engine_timing') != build['binary_sha256'] or package['binary_sha256'] != build['binary_sha256']:
        raise ValueError('Binary binding differs')
    for relative, expected in package['files'].items():
        if sha(args.package / relative) != expected:
            raise ValueError('Delivery file changed: ' + relative)
    offline = load(args.evidence / 'offline-r3/result.json')
    linux = load(args.evidence / 'linux-native/result.json')
    if offline['status'] != 'offline_contracts_passed' or linux['status'] != 'Linux_thread_CPU_rusage_contracts_passed':
        raise ValueError('Offline checks not completed')
    output = args.evidence / 'delivery-review.json'
    if output.exists():
        raise FileExistsError('Preserve previous delivery review')
    result = {'status': 'development_delivery_verified_not_board_executed',
              'formal_locked_files_unchanged': len(lock['build_files']),
              'baseline_lock_sha256': sha(ROOT / 'software/demo/baseline-lock.json'),
              'source_manifest_sha256': sha(args.source / 'source-manifest.json'),
              'build_result_sha256': sha(args.build / 'build-result.json'),
              'package_sha256': sha(args.package / 'package.json'),
              'binary_sha256': build['binary_sha256'], 'delivery_files_verified': len(package['files']),
              'Python_analysis_tests': 13, 'SDK_free_native_contract_cases': ['basic', 'thread', 'capacity'],
              'Windows_and_FPAI_Linux_contracts_passed': True,
              'ARM64_compiled': True, 'board_or_model_executed': False,
              'old_DATA_investigation_resumed': False,
              'NPU_pure_compute_and_DDR_stalls_measured': False,
              'SDK_tuple_unit_confirmed': False, 'hardware_ordinal_mapping_confirmed': False,
              'tool_sources': {p.name: sha(p) for p in sorted(HERE.glob('*')) if p.is_file()},
              'build_steps': load(args.build / 'build-steps.json')}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], 'formal locked files unchanged:', result['formal_locked_files_unchanged'])


if __name__ == '__main__':
    main()
