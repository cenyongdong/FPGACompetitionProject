"""R7-only actual synthesis gate; --check-only never evaluates EDA results."""
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
    spec = importlib.util.spec_from_file_location('r7_synthesis_public_contract', CONTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    helper = contract()
    if args.check_only:
        _, proof = helper.constraints_algorithms()
        print(json.dumps({'check_only': True, 'EDA_started': False, 'actual_synthesis_gate_run': False,
                          'fixed_algorithm_adapter': proof}, indent=2))
        return
    directory = helper.E / 'read-v3r7-synthesis'
    helper.need(not (directory / 'review.json').exists(), 'Preserve previous synthesis review')
    review = helper.verify_synthesis()
    review.update(actual_adapter_SHA256=helper.sha(Path(__file__)), r7_contract_SHA256=CONTRACT_SHA,
                  scope='new actual r7 synthesis and sources only; not constraints/physical/board acceptance')
    helper.save_new(directory / 'review.json', review)
    print(json.dumps({'passed': True, 'candidate_run': 'synth_read_v3r7', 'actual_board_acceptance': False}))


if __name__ == '__main__':
    main()
