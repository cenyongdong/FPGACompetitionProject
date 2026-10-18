"""R7-only constraints adapter using the complete frozen CDC/clock algorithm."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

CONTRACT = Path(__file__).with_name('ai_read_r9_contract.py')
CONTRACT_SHA = 'd4212dfa4f917a1e44327442e25421a771773448be358fa84f6ecf96e96b4dc1'


def contract():
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != CONTRACT_SHA:
        raise ValueError('Frozen r9 identity/report contract changed')
    spec = importlib.util.spec_from_file_location('r9_constraints_public_contract', CONTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    helper = contract()
    algorithms, adaptation = helper.constraints_algorithms()
    if args.check_only:
        print(json.dumps({'check_only': True, 'EDA_started': False, 'actual_constraint_gate_run': False,
                          'fixed_algorithm_adapter': adaptation}, indent=2))
        return
    directory = helper.E / 'read-v3r9-constraints'
    helper.need(not (directory / 'review.json').exists() and not (directory / 'common-constraints-review.json').exists(),
                'Preserve previous r9 constraint review')
    synthesis = helper.verify_synthesis()
    algorithms.main()
    common = directory / 'common-constraints-review.json'
    review = helper.load(common)
    helper.need(review.get('route_prerequisite_pass') is True and review['read_bits'] == 2768
                and review['actual_clock_taps']['clock_groups_checked'] == 21,
                'New r9 2768-bit/21-group constraint contract differs')
    review.update(candidate_run='impl_read_v3r9', managed_run=True,
                  source_preparation_review_SHA256=helper.sha(helper.PREPARATION),
                  synthesis_identity=synthesis, actual_adapter_SHA256=helper.sha(Path(__file__)),
                  r9_contract_SHA256=CONTRACT_SHA, common_constraints_review_SHA256=helper.sha(common),
                  fixed_algorithm_adapter=adaptation, old_constraint_pass_reused=False)
    helper.save_new(directory / 'review.json', review)
    print(json.dumps({'route_prerequisite_pass': True, 'candidate_run': 'impl_read_v3r9',
                      'new_BOOT_or_reboot_authorized': False}))


if __name__ == '__main__':
    main()
