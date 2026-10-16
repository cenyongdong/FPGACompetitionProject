"""Gate local bit generation from actual routed evidence, retaining raw failures."""
from pathlib import Path
import collections
import hashlib
import json
import re

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
F = R / '.local/hdmi-integration-20261016-r1/reference'
O = E / 'system-route-r5'
P = E / 'system-route-r5-reports'
assert not (O / 'review.json').exists()
for stage in ['system-route-r5', 'system-route-r5-reports', 'mailbox-enable-r5']:
    assert json.loads((E / stage / 'execution.json').read_text())['exit'] == 0, stage
text = (P / 'timing-summary.rpt').read_text(encoding='utf-8')
lines = text.splitlines()
index = next(i for i, line in enumerate(lines) if line.startswith('    WNS(ns)'))
values = lines[index + 2].split()
assert len(values) == 12, values
wns, tns, whs, ths, wpws, tpws = [float(values[i]) for i in [0, 1, 4, 5, 8, 9]]
assert wns >= 0 and whs >= 0 and tns == ths == 0
assert values[2] == values[6] == '0' and values[10] == '2'
assert wpws == -0.409 and tpws == -0.479
prefix = 'U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/'
pulse = [line for line in lines if line.startswith('Min Period') and re.search(r'\s-0\.', line)]
assert len(pulse) == 2
for endpoint, required, slack in [('clkout1_buf/I', '1.409', '-0.409'),
                                  ('plle2_adv_inst/CLKOUT0', '1.071', '-0.071')]:
    matches = [line for line in pulse if line.endswith(prefix + endpoint)]
    assert len(matches) == 1 and required in matches[0] and slack in matches[0]
assert 'There are 0 register/latch pins with no clock.' in text
assert 'There are 0 pins that are not constrained for maximum delay.' in text
child = F / 'fpai_demo_vivado.runs/impl_hdmi_r5'
drc = (child / 'ai7030_edif_top_drc_routed.rpt').read_text(encoding='utf-8')
assert not re.findall(r'^\S+#\d+ Error$', drc, re.M)
assert 'REQP-1580#' not in drc and 'UTLZ-1#' not in drc
assert 'The following rules are disabled: REQP-44, REQP-46, REQP-52, REQP-56' in drc
reopened = (P / 'DRC-reopened-default-profile.rpt').read_text(encoding='utf-8')
assert re.findall(r'^(\S+#\d+) Error$', reopened, re.M) == ['REQP-52#1', 'REQP-56#1']
skew = (P / 'bus-skew.rpt').read_text(encoding='utf-8')
assert 'VIOLATED' not in skew
gray = []
for block in skew.split('Slack '):
    if 'Endpoint Source:' not in block:
        continue
    source = block.split('Endpoint Source:', 1)[1].splitlines()[0].strip()
    if '/hdmi_display/' not in source:
        continue
    actual = float(re.search(r'Actual Bus Skew:\s+([\d.]+)ns', block)[1])
    bound = float(re.search(r'Requirement:\s+([\d.]+)ns', block)[1])
    slack = float(re.match(r'\(MET\)\s*:\s*([\d.]+)ns', block)[1])
    assert actual <= bound and slack >= 0
    gray.append({'source': source, 'actual_skew_ns': actual, 'bound_ns': bound, 'slack_ns': slack})
assert len(gray) == 3
bounds = (P / 'mailbox-routed-bounds.txt').read_text().splitlines()
assert len(bounds) == 2
for row, name, requirement in zip(bounds, ['command', 'response'], [5., 10.]):
    assert row.startswith(name + '|')
    assert float(re.search(r'requirement=([\d.]+)', row)[1]) == requirement
    assert float(re.search(r'slack=([\d.-]+)', row)[1]) >= 0
ce = (E / 'mailbox-enable-r5/CE-paths.txt').read_text().splitlines()
assert len(ce) == 96 and all('|requirement=5.000|' in row for row in ce)
ce_min = min(float(re.search(r'slack=([\d.-]+)', row)[1]) for row in ce)
assert ce_min >= 0
physical = (P / 'HDMI-clock-physical.txt').read_text()
assert physical.count('|OSERDESE2|') == 8
assert physical.count('/CLK|serial_raw') == physical.count('/CLKDIV|pixel_clk') == 8
assert '|BUFIO|BUFIO_X0Y1|' in physical and '|BUFR|BUFR_X0Y1|' in physical
assert '|MMCME2_ADV|MMCME2_ADV_X0Y0|' in physical
rows = (P / 'HDMI-CDC-rows.txt').read_text(encoding='utf-8').splitlines()
counts = dict(collections.Counter(re.search(r'CDC-\d+', row)[0] for row in rows))
assert counts == {'CDC-10':5, 'CDC-3':5, 'CDC-15':207, 'CDC-6':3, 'CDC-1':107, 'CDC-12':2}
assert all('/mailbox/payload_hold_reg' in row for row in rows if re.search(r'\bCDC-1\s', row))
sources = json.loads((E / 'constraint-binding-r5/review.json').read_text())['bound_source_sha256']
for relative, expected in sources.items():
    assert hashlib.sha256((F / relative).read_bytes()).hexdigest() == expected, relative
assert (F / 'constrs_1/hdmi_cdc.tcl').read_bytes() == (F / 'constrs_1/hdmi_cdc.xdc').read_bytes()
review = {
    'bit_generation_prerequisite_pass': True,
    'scope': 'Generate local candidate for phased controlled board testing; not full-system CDC, electrical HDMI or live replacement acceptance',
    'global_setup_WNS_ns': wns, 'global_hold_WHS_ns': whs, 'TNS_ns': tns, 'THS_ns': ths,
    'raw_timing_pass': False, 'unchanged_user_exception_MinPeriod_rows': pulse,
    'Gray_bus_skew': gray, 'mailbox_data_response_actual': bounds,
    'mailbox_enable_CE_paths': len(ce), 'mailbox_CE_min_slack_ns': ce_min,
    'HDMI_CDC_row_counts_not_fault_counts': counts,
    'manual_CDC_review': 'ROUTED-CDC-REVIEW.md',
    'factory_DRC_profile_errors': 0,
    'reopened_default_profile_errors_retained': ['REQP-52#1', 'REQP-56#1'],
    'remaining_warnings': [
        'REQP-1577 feedback BUFG vs BUFIO/BUFR: all eight serializer CLK/CLKDIV use the same raw-output BUFIO/BUFR branch; routed setup/hold positive. No severity override. External eye and monitor remain unverified.',
        'New placement PDRC-62 two/PDRC-63 one dangling O5 warnings retained; no severity override or claim of zero warnings.',
        'Original MIG non-dedicated clock, SDI gated clock and pre-existing AI CDC/BRAM warnings retained; not independently signed off by this HDMI work.',
    ],
    'source_sha256': sources,
    'board_download_or_reboot_authorized_by_this_review': False,
}
(O / 'ROUTED-CDC-REVIEW.md').write_text('''# Routed HDMI CDC review

This review permits local candidate generation for the already approved staged test. It does not turn the whole design's generic CDC report into a pass.

The 107 CDC-1 rows all originate in payload_hold. The 207 CDC-15 rows are handshake-controlled payload/response captures. The source holds command data until a two-stage synchronized response returns; the target holds its response until the next accepted request. Request/response toggles use two ASYNC_REG stages. Actual data limits remain 5ns/10ns; 96 command-driven CE endpoints separately retain 5ns, worst slack +0.856ns. No data or CE constraint was changed for this review.

The three CDC-6 buses are registered binary-to-Gray pointers/counter with two receiving stages. They retain source-period max-delay and skew constraints; all three routed skew checks pass. Neither binary counter buses nor unregistered Gray conversion are directly sampled.

CDC-10/12 reset rows terminate at the three intentional asynchronous assertion / three-stage local release chains. Only their nine CLR pins are cut. Eighty FIFO functional state resets were traced to their own-domain release chain in synthesis; functional recovery/removal remain timed and routed global setup/hold have no failures. Original negative recovery/removal reports are preserved.

The other CDC-10 rows are combinational run/idle flags entering two ASYNC_REG stages. Running is running && !stopping; START arms at a frame boundary, STOP/fault prevents subsequent requests and drains accepted reads. Idle requires stopping and no running/frame/waiting/reader activity. CSR idle is diagnostic only and cannot authorize frame release. Bars cannot be re-enabled after the first START. Release requires the atomic mailbox snapshot and stopped ID, never a separately synchronized idle bit. The r8 full-pixel/underflow/drain/stopped-pixel-clock tests remain the applicable logic evidence; this is not a measured MTBF or arbitrary reset-sequence guarantee.

All eight OSERDES CLK/CLKDIV pins use serial_raw/pixel_clk from the same MMCM output through adjacent BUFIO/BUFR resources. REQP-1580 is absent. REQP-1577 feedback buffering warning remains active: internal relative clock checks and real-model PHY simulation pass, while external eye/monitor operation still require actual board testing. No new check severity or timing exception was added.
''', encoding='utf-8')
(O / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
print(json.dumps({k:v for k,v in review.items() if k != 'source_sha256'}, indent=2))
