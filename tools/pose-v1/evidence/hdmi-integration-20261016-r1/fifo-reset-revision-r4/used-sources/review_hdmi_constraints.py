"""Check actual constraints before routing. This is not CDC/board signoff."""
from pathlib import Path
import hashlib, json, re, collections, sys

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
F = R / '.local/hdmi-integration-20261016-r1/reference'
revision = sys.argv[1] if len(sys.argv)>1 else 'r4'
assert revision in ('r4', 'r5')
O = E / ('constraint-binding-' + revision)
assert json.loads((O / 'execution.json').read_text())['exit'] == 0
log = (O / 'stdout.txt').read_text(encoding='utf-8', errors='replace')
drc = (O / 'DRC.rpt').read_text(encoding='utf-8')
checks = (O / 'mailbox-bound-check.txt').read_text(encoding='utf-8').splitlines()
assert 'ERROR:' not in log and '18-515' not in log
assert 'UTLZ-1' not in drc and 'REQP-1580' not in drc
errors = re.findall(r'^([\w-]+)#\d+ Error$', drc, re.M)
assert errors == ['NDRV-1', 'NDRV-1'], errors
assert 'S1_AXI_HP_HC_WID[4:0]' in drc and 'pl_int_ready' in drc
assert len(re.findall(r'^REQP-1577#', drc, re.M)) == 1
assert 'hdmi_display/clock_generator/feedback_raw' in drc
assert log.count('\nHDMI_FACTORY_CUT_SCOPED ') == 2
assert log.count('\nHDMI_GRAY_BOUND ') == 3
if revision == 'r5':
    assert log.count('\nHDMI_ASYNC_RESET_CHAIN_INPUT_ONLY ') == 3
    assert '\nHDMI_FIFO_STATE_RESET_LOCAL_CLOCK_PROOF ' in log
    assert len((O / 'FIFO-local-reset-drivers.txt').read_text().splitlines()) >= 40
for name, requirement in [('command', '5.000'), ('response', '10.000')]:
    rows = [line for line in checks if line.startswith(name + '|')]
    assert rows, name
    assert all(abs(float(re.search(r'requirement=([\d.]+)', line)[1]) - float(requirement)) < 0.001 for line in rows)
cdc_rows = [line for line in (O / 'CDC.rpt').read_text(encoding='utf-8').splitlines()
            if 'hdmi_display/' in line and re.match(r'^\s*\d+\s+CDC-', line)]
response_rows = [line for line in cdc_rows if '/mailbox/response_hold_reg' in line and '/mailbox/source_response_reg' in line]
assert response_rows and all('Max Delay Datapath Only' in line for line in response_rows)
(O / 'HDMI-CDC-rows.txt').write_text('\n'.join(cdc_rows) + '\n', encoding='utf-8')
paths = list((F / 'rtl/hdmi_candidate').glob('*'))
paths += [F / p for p in ['rtl/ai7030_edif_top.v', 'rtl/ps_ai_peripheral.sv',
    'rtl/display/frame_to_ps_largebuf.v', 'rtl/display/uihdmitx.v',
    'rtl/display/oserdese2_10to1.v', 'constrs_1/hdmi_cdc.xdc', 'constrs_1/ai7030.xdc']]
review = {
    'route_prerequisite_pass': True,
    'not_full_timing_CDC_or_board_acceptance': True,
    'old_synth_NDRV_two_items_preserved_for_factory_opt_review': True,
    'remaining_HDMI_DRC_warning': 'REQP-1577 feedback BUFG differs from BUFIO/BUFR outputs. Both serializer clocks use the same output branch; no REQP-1580 remains. Actual routed clock/hold checks still required, no severity/DRC waiver applied.',
    'mailbox_explicit_requirements_ns': {'command': 5, 'response': 10},
    'new_CDC_row_counts_not_independent_fault_counts': dict(collections.Counter(re.search(r'CDC-\d+', line)[0] for line in cdc_rows)),
    'remaining_review': ['Routed timing including resets, mailbox bounds and Gray skew',
                         'Physical BUFIO/BUFR regional placement and serializer clock alignment',
                         'Only the two unchanged AI minimum-period checks have user exceptions',
                         'Pre-download resource isolation and current hardware identity'],
    'bound_source_sha256': {p.relative_to(F).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()},
}
assert not (O / 'review.json').exists()
(O / 'review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k:v for k,v in review.items() if k != 'bound_source_sha256'}))
