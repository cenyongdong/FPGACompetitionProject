"""Release the local HP2 candidate from native physical reports, without board IO."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('evidence', type=Path)
    cli.add_argument('checkpoint', type=Path)
    args = cli.parse_args()
    e = args.evidence.resolve()
    for stage in ('synthesis', 'route', 'final'):
        require(json.loads((e / (stage + '-execution.json')).read_text())['exit_code'] == 0,
                'Inspect native ' + stage + ' result before releasing the bit')
    require(args.checkpoint.is_file(), 'Final routed checkpoint missing')
    text = (e / 'timing-final.rpt').read_text()
    lines = text.splitlines()
    header = next(i for i, s in enumerate(lines) if 'WNS(ns)' in s and 'TNS(ns)' in s)
    values = next(s.split() for s in lines[header + 1:] if re.match(r'^\s*-?\d+\.\d+\s', s))
    require(len(values) == 12, 'Unrecognized native timing summary: inspect the report')
    wns, tns, whs, ths = (float(values[i]) for i in (0, 1, 4, 5))
    require(wns >= 0 and whs >= 0 and tns == ths == 0 and values[2] == values[6] == '0',
            'Setup/hold timing failed')
    require(re.search(r'There are\s+0\s+pins that are not constrained for maximum delay\.', text),
            'Internal maximum-delay constraints incomplete')
    require(re.search(r'There are\s+0\s+register/latch pins with no clock\.', text),
            'Register clocks incomplete')
    prefix = 'U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/'
    allowed = {prefix + 'clkout1_buf/I': (1.409, 1.0, -0.409),
               prefix + 'plle2_adv_inst/CLKOUT0': (1.071, 1.0, -0.071)}
    failed_pulses = []
    for line in lines:
        m = re.search(r'\s(-\d+\.\d+)\s+\S+\s+(\S+)\s*$', line)
        if not m or not re.match(r'^(Min Period|Max Period|Low Pulse Width|High Pulse Width)\s', line):
            continue
        endpoint = m[2]
        require(line.startswith('Min Period') and endpoint in allowed,
                'New pulse-width/minimum-period failure: ' + line)
        numeric = [float(s) for s in line.split() if re.fullmatch(r'-?\d+\.\d+', s)]
        require(tuple(numeric) == allowed[endpoint], 'Original AI period exception changed')
        failed_pulses.append(line)
    require(len(failed_pulses) == 2 and int(values[10]) == 2,
            'Expected only the two previously approved AI period exceptions')
    facts = [s.split('\t') for s in (e / 'final-native-facts.tsv').read_text().splitlines()]
    require(['PART', 'xc7z030ffg676-2'] in facts, 'Wrong native target')
    ready = [s for s in facts if s[0] == 'READY']
    require(ready and all(abs(float(s[-2]) - 5.0) <= 0.001 and float(s[-1]) >= 0 for s in ready),
            'New readiness path absent, cut, failing, or not on the existing 5ns clock')
    skew = (e / 'bus-skew-final.rpt').read_text()
    require('VIOLATED' not in skew, 'Bus-skew failure')
    route = (e / 'route-status-final.rpt').read_text()
    require(re.search(r'# of nets with routing errors\.+\s*:\s*0\s*:', route), 'Routing errors remain')
    drc = (e / 'drc-final.rpt').read_text()
    errors = re.findall(r'^(\S+#\d+)\s+Error\s*\n(.*?)(?=^\S+#\d+\s|\Z)', drc, re.M | re.S)
    gt_objects = {'REQP-52': 'rx_sdi_inst/SDI0/SDI/GTX_i/gtxe2_i',
                  'REQP-56': 'rx_sdi_inst/gtxe2_common_0/gtxe2_common_i'}
    for name, block in errors:
        rule = name.split('#')[0]
        cells = re.findall(r'\bcell\s+(\S+?):', block)
        require(rule in gt_objects and cells == [gt_objects[rule]], 'New default-profile DRC error: ' + name)
    require('Fully Routed' in drc, 'Physical design is not fully routed')
    overlay = json.loads((e / 'source-overlay.json').read_text())
    for original, used in overlay['replacements'].items():
        if original.replace('\\', '/').endswith('/bd/ps_ai/synth/ps_ai.v'):
            require(Path(original).read_bytes() == Path(used).read_bytes(),
                    'Actual generated BD source differs from the recorded overlay')
    sources = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
               for p in overlay['replacements'].values()}
    review = dict(bit_generation_prerequisite_pass=True, raw_timing_pass=False,
                  WNS_ns=wns, WHS_ns=whs, TNS_ns=tns, THS_ns=ths,
                  pulse_exception_rows=failed_pulses, readiness_paths=ready,
                  raw_DRC_errors=[name for name, _ in errors],
                  allowed_disabled_DRC=['REQP-44', 'REQP-46', 'REQP-52', 'REQP-56'],
                  unconstrained_internal_endpoints=0, bus_skew_violations=0,
                  checkpoint=str(args.checkpoint.resolve()), source_sha256=sources,
                  source_selection='source-overlay.json; actual BD-generated ps_ai.v plus two wrapper overlays',
                  legacy_IO_limits='11 inputs and 6 outputs without delays remain; no new external ports',
                  board_tested=False, new_BOOT_or_reboot_authorized=False)
    (e / 'qualification.json').write_text(json.dumps(review, indent=2))
    print(json.dumps(dict(bit_generation_prerequisite_pass=True, WNS_ns=wns, WHS_ns=whs)))


if __name__ == '__main__':
    main()
