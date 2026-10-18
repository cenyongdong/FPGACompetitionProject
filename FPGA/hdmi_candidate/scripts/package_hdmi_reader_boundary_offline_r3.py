"""R7 offline ICAP/BOOT/bundle adapter; pure, fail-closed default inspect."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ENTRY = Path(__file__).resolve()
RELEASE = ENTRY.with_name('ai_read_r9_native_release_r3.py')


def check_entry_sources(frozen):
    for path, raw in frozen.items():
        if Path(path).read_bytes() != raw:
            raise ValueError('Actual executed r9 packager/helper source changed: ' + str(path))


def release(raw=None):
    frozen = RELEASE.read_bytes() if raw is None else raw
    spec = importlib.util.spec_from_file_location('r9_package_public_release', RELEASE)
    result = importlib.util.module_from_spec(spec)
    exec(compile(frozen, str(RELEASE), 'exec'), result.__dict__)
    return result


def prepared(entry_bytes=None, helper_bytes=None):
    entry_bytes = ENTRY.read_bytes() if entry_bytes is None else entry_bytes
    helper_bytes = RELEASE.read_bytes() if helper_bytes is None else helper_bytes
    frozen = {ENTRY: entry_bytes, RELEASE: helper_bytes}
    check_entry_sources(frozen)
    helper = release(helper_bytes)
    common, adaptation, raw, adapted = helper.package_algorithms()
    base_stage = common.Stage

    class ArchivedR7Stage(base_stage):
        def __init__(self, mode):
            check_entry_sources(frozen)
            super().__init__(mode)
            for name, data in [('actual-r9-packager-adapter.py', entry_bytes),
                               ('actual-r9-release-helper.py', helper_bytes),
                               ('base-packager-algorithms.py', raw),
                               ('adapted-packager-algorithms.py', adapted)]:
                self.save(name, data)
            common.dump(self.out / 'package-algorithm-adapter.json', adaptation)
            for path, digest in helper.source_closure().items():
                self.read(Path(path), digest)
            for path, frozen_raw in frozen.items():
                self.read(path, hashlib.sha256(frozen_raw).hexdigest())

        def check_inputs(self):
            check_entry_sources(frozen)
            super().check_inputs()
            check_entry_sources(frozen)

        def procise(self, code):
            check_entry_sources(frozen)
            try:
                result = super().procise(code)
            except BaseException:
                try:
                    check_entry_sources(frozen)
                except Exception as error:
                    try:
                        self.save('source-change-after-original-failure.json',
                                  json.dumps({'source_error': str(error),
                                              'original_failure_rethrown': True}).encode())
                    except Exception:
                        pass  # Saving diagnostics must not replace the original tool failure.
                raise
            check_entry_sources(frozen)
            return result

        def gate(self):
            evidence = {}
            self.bit_gate = helper.verify_bit_release(evidence)
            for path, digest in evidence.items():
                self.read(Path(path), digest)
            if self.mode in ('boot', 'bundle'):
                patch = self.json(helper.E / 'read-v3-icap/review.json')
                helper.need(patch.get('r9_bit_gate') == self.bit_gate,
                            'ICAP predecessor belongs to a different r9 release')
            if self.mode == 'bundle':
                boot = self.json(helper.E / 'read-v3-boot/review.json')
                helper.need(boot.get('r9_bit_gate') == self.bit_gate,
                            'BOOT predecessor belongs to a different r9 release')
            common.dump(self.out / 'r9-bit-gate.json', self.bit_gate)

    original_boot = common.boot

    def archived_boot(stage):
        original_boot(stage)
        # Add source identity after the complete unchanged BOOT byte algorithm.
        review = common.json.loads((stage.out / 'review.json').read_text(encoding='utf-8'))
        helper.need('r9_bit_gate' not in review, 'Unexpected BOOT release field')
        review['r9_bit_gate'] = stage.bit_gate
        common.dump(stage.out / 'review.json', review)

    adaptation['runtime_gate_replacement'] = (
        'Only Stage.gate replaced: exact current r9 fullflow/report/bit/context/derived release; '
        'all original baseline, ICAP, BOOT, bundle, software/model/SDK algorithms retained')
    adaptation['runtime_output_extension'] = 'BOOT review adds exact current r9_bit_gate after unchanged byte checks'
    adaptation['executed_entry_source_freeze'] = (
        'adapter/helper bytes frozen before first pure gate; compile/archive those exact bytes; '
        'compare current bytes before directory/tool and after tool/final input checks')
    common.execution_namespace['Stage'] = ArchivedR7Stage
    common.execution_namespace['boot'] = archived_boot
    return common, adaptation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'icap', 'boot', 'bundle'], nargs='?', default='inspect')
    args = parser.parse_args()
    entry_bytes, helper_bytes = ENTRY.read_bytes(), RELEASE.read_bytes()
    frozen = {ENTRY: entry_bytes, RELEASE: helper_bytes}
    check_entry_sources(frozen)
    helper = release(helper_bytes)
    # Actual complete routed/bit proof precedes even Stage's fresh directory.
    bit_gate = helper.verify_bit_release()
    check_entry_sources(frozen)
    common, adaptation = prepared(entry_bytes, helper_bytes)
    if args.mode == 'inspect':
        print(json.dumps({'inspect_only': True, 'tools_started': False, 'board_executed': False,
                          'r9_bit_gate': bit_gate, 'adaptation': adaptation}, indent=2))
        check_entry_sources(frozen)
        return 0
    prior = sys.argv
    sys.argv = [str(helper.PACKAGE_BASE), args.mode]
    try:
        result = common.main()
        check_entry_sources(frozen)
        return result
    finally:
        sys.argv = prior


if __name__ == '__main__':
    raise SystemExit(main())
