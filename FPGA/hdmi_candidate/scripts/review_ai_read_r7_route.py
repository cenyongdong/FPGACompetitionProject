"""R7-only full routed gate; all actual STA/DRC/CDC/HDMI algorithms retained."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

CONTRACT = Path(__file__).with_name('ai_read_r7_contract.py')
CONTRACT_SHA = 'fa28b01f12baf593788d554fae942564ff69753caf1310cd034a48d08178fdc8'


def contract():
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != CONTRACT_SHA:
        raise ValueError('Frozen r7 identity/report contract changed')
    spec = importlib.util.spec_from_file_location('r7_route_public_contract', CONTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    helper = contract()
    evaluate, adaptation = helper.routed_report_algorithm()
    algorithms, _ = helper.constraints_algorithms()
    if args.check_only:
        print(json.dumps({'check_only': True, 'EDA_started': False, 'actual_routed_gate_run': False,
                          'unchanged_report_algorithm': adaptation}, indent=2))
        return
    directory = helper.E / 'read-v3r7-reports'
    helper.need(not (directory / 'review.json').exists(), 'Preserve previous r7 routed review')
    lineage = helper.verify_fullflow()
    gate = helper.load(helper.E / 'read-v3r7-constraints/review.json')
    sources, installed = helper.stable_sources(), helper.installed_identity()
    review = evaluate(directory, helper.NATIVE, gate, algorithms, sources, helper.INSTALLED, installed,
                      lineage['actual_phase_identity_evidence_SHA256'], helper.CONSTRAINTS)
    helper.need(review.get('bit_generation_prerequisite_pass') is True and review['read_bits'] == 2768,
                'Complete new r7 routed gate did not pass')
    review.update(candidate_run='impl_read_v3r7', managed_run=True, fresh_fullflow=lineage,
                  source_preparation_review_SHA256=helper.sha(helper.PREPARATION),
                  actual_adapter_SHA256=helper.sha(Path(__file__)), r7_contract_SHA256=CONTRACT_SHA,
                  fixed_report_algorithm=adaptation, old_report_pass_reused=False,
                  r6_postroute_optimization_inherited=False)
    helper.save_new(directory / 'review.json', review)
    print(json.dumps({'bit_generation_prerequisite_pass': True, 'candidate_run': 'impl_read_v3r7',
                      'new_BOOT_or_reboot_authorized': False}))


if __name__ == '__main__':
    main()
