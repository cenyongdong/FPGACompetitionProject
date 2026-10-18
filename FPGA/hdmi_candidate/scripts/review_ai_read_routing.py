"""Bounded, read-only EDIF/RTL routing review; no EDA, SDK or board access.

Writes only a fresh evidence directory. Truth tables cover the named LUTs and
their exact connections, not reachable states, a whole-design equivalence proof,
or a diagnosis of the board failure. No VMA/configuration value is assumed.
"""
from pathlib import Path
from itertools import product
import argparse
import bisect
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / '.local/hdmi-live-20261017-r1/reference'
IDENTITY = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/static-read-path/source-identity.json'
EDIF = 'rtl/edif/AI_Mate.edif'
PS = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v'
EXPECTED = {
    EDIF: '38f14b4427244f49a1ff0edf9dcdfe4438d033807d76018c688aa218c491d49c',
    PS: 'b253cc32badb6bc182e3dfce3e5732b43229d6d93ca07e2d98b582783700a5e2',
}
PRIMITIVES = {f'LUT{i}' for i in range(1, 7)} | {'FDRE', 'FDCE', 'CARRY4'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Cell:
    """Parse only one named cell, retaining original offsets for raw excerpts."""

    def __init__(self, source, name):
        cells = list(re.finditer(r'\(cell (\w+) \(celltype', source))
        matches = [i for i, m in enumerate(cells) if m[1] == name]
        require(len(matches) == 1, f'unique cell required: {name}')
        i = matches[0]
        self.base = cells[i].start()
        self.name = name
        self.text = source[self.base:cells[i + 1].start() if i + 1 < len(cells) else len(source)]
        self.instances, self.nets, self.by_pin = {}, {}, {}
        ims = list(re.finditer(r'\(instance (?:\(rename (\S+) "([^"]+)"\)|(\S+))', self.text))
        first_net = self.text.find('(net ')
        for j, m in enumerate(ims):
            end = ims[j + 1].start() if j + 1 < len(ims) else first_net
            block = self.text[m.start():end]
            ref = re.search(r'\(cellref (\S+)', block)
            init = re.search(r'\(property INIT \(string "([^"]+)"', block)
            key = m[1] or m[3]
            self.instances[key] = {'name': m[2] or m[3], 'ref': ref[1] if ref else None,
                                   'init': init[1] if init else None,
                                   'span': (self.base + m.start(), self.base + end)}
        ns = list(re.finditer(r'\(net (?:\(rename (\S+) "([^"]+)"\)|(\S+))', self.text))
        for j, m in enumerate(ns):
            end = ns[j + 1].start() if j + 1 < len(ns) else len(self.text)
            block = self.text[m.start():end]
            key = m[1] or m[3]
            pins = re.findall(r'\(portref (\w+|\(member \w+ \d+\)) \(instanceref (\w+)\)\)', block)
            self.nets[key] = {'label': m[2] or key, 'pins': pins,
                              'span': (self.base + m.start(), self.base + end)}
            for pin, instance in pins:
                require((instance, pin) not in self.by_pin, f'duplicate pin: {name}/{instance}/{pin}')
                self.by_pin[instance, pin] = key

    def instance(self, display_name):
        keys = [k for k, v in self.instances.items() if v['name'] == display_name]
        require(len(keys) == 1, f'unique instance required: {self.name}/{display_name}')
        key = keys[0]
        pins = {p: self.nets[n]['label'] for (i, p), n in self.by_pin.items() if i == key}
        return key, self.instances[key], pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3/read-routing-review')
    args = parser.parse_args()
    out = args.output.resolve()
    evidence_root = (ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3').resolve()
    require(out.parent == evidence_root, 'output must be a direct child of the r3 evidence directory')
    require(not out.exists(), f'refusing to overwrite: {out}')
    out.mkdir()
    started = time.monotonic()
    review = {'passed': False, 'scope': 'named routing connections and exhaustive small LUT tables only',
              'execution_location': 'Windows host; D:/FPGACompetitionProject',
              'board_access': False, 'EDA_or_SDK_invocation': False,
              'VMA_value_assumed': False, 'CPU_physical_mapping_proven': False,
              'board_root_cause_proven': False, 'limits': {'max_EDIF_bytes': 100 * 1024 * 1024,
              'max_truth_table_rows_per_check': 256, 'max_total_excerpt_bytes': 2 * 1024 * 1024},
              'checks': [], 'sources': {}, 'excerpts': [], 'truth_tables': []}
    sources = {}
    newlines = {}
    spans_saved = set()
    excerpt_bytes = 0

    def excerpt(source_name, span, reason):
        nonlocal excerpt_bytes
        start, end = span
        if (source_name, start, end) in spans_saved:
            return
        spans_saved.add((source_name, start, end))
        raw = sources[source_name][start:end].encode('ascii')
        excerpt_bytes += len(raw)
        require(excerpt_bytes <= review['limits']['max_total_excerpt_bytes'], 'excerpt bound exceeded')
        filename = f'excerpt-{len(review["excerpts"]):03d}.txt'
        (out / filename).write_bytes(raw)
        review['excerpts'].append({'file': filename, 'source': source_name, 'reason': reason,
                                  'line_start': bisect.bisect_right(newlines[source_name], start) + 1,
                                  'line_end': bisect.bisect_right(newlines[source_name], end - 1) + 1,
                                  'byte_start': start, 'byte_end_exclusive': end, 'SHA256': sha(raw)})

    def inspect(cell, name):
        key, instance, pins = cell.instance(name)
        excerpt(EDIF, instance['span'], f'{cell.name}/{name} declaration and INIT')
        for pin, net in cell.by_pin.items():
            if pin[0] == key and cell.nets[net]['label'] not in ('<const0>', '<const1>'):
                excerpt(EDIF, cell.nets[net]['span'], f'{cell.name}/{name}/{pin[1]} wiring')
        return instance, pins

    def table(cell, name, expected_init, wiring, variables, expected):
        instance, pins = inspect(cell, name)
        require(instance['ref'] == f'LUT{len(wiring)}', f'wrong LUT type: {name}')
        require(instance['init'] == expected_init, f'wrong INIT: {name}')
        require(all(pins.get(pin) == net for pin, net in wiring.items()), f'wiring changed: {name}: {pins}')
        init = int(expected_init.split("'h")[1], 16)
        rows = []
        for values in product((0, 1), repeat=len(variables)):
            environment = dict(zip(variables, values))
            address = sum(environment[net] << int(pin[1:]) for pin, net in wiring.items())
            actual = (init >> address) & 1
            wanted = int(expected(environment))
            rows.append({'inputs': environment, 'INIT_index': address, 'actual': actual, 'expected': wanted})
            require(actual == wanted, f'truth table failed: {name}: {environment}')
        require(len(rows) <= 256, 'truth table bound exceeded')
        review['truth_tables'].append({'cell': cell.name, 'instance': name, 'ref': instance['ref'],
                                      'INIT': expected_init, 'rows': rows, 'passed': True})

    try:
        identity_bytes = IDENTITY.read_bytes()
        identity = {x['path']: x for x in json.loads(identity_bytes)}
        review['r2_identity_manifest'] = {'path': str(IDENTITY), 'SHA256': sha(identity_bytes)}
        (out / 'r2-source-identity.json').write_bytes(identity_bytes)
        for rel, expected_hash in EXPECTED.items():
            path = REFERENCE / rel
            require(path.stat().st_size <= 100 * 1024 * 1024, f'source size bound exceeded: {rel}')
            raw = path.read_bytes()
            require(sha(raw) == expected_hash, f'actual source identity changed: {rel}')
            previous = identity[rel]
            require(previous['original_sha256'] == previous['candidate_sha256'] == expected_hash
                    and previous['byte_equal'] is True, f'r2 source identity mismatch: {rel}')
            sources[rel] = raw.decode('ascii')
            newlines[rel] = [m.start() for m in re.finditer('\n', sources[rel])]
            review['sources'][rel] = {'path': str(path), 'SHA256': expected_hash, 'bytes': len(raw),
                                     'matches_r2_original_and_candidate': True}
        edif = sources[EDIF]
        top, mux = Cell(edif, 'AI_Mate'), Cell(edif, 'dmux4')
        addr = 'u_AI_Mate_top/ddr_rd_itf\\.araddr[32]'
        full = 'u_AI_Mate_top/u_pspl_split/reg_fifo_u0/full'
        v0 = 'u_AI_Mate_top/ddr_ritcn_u0/avr_rs_u0/u_avr_brs/valid_tmp0'
        v1 = 'u_AI_Mate_top/ddr_ritcn_u0/avr_rs_u0/s_valid_frs'
        wiring = {'I0': v0, 'I1': v1, 'I2': full, 'I3': addr}
        table(top, 'U0_ddr2hp_itcn_i_3', "16'h0E00", wiring, [addr, full, v0, v1],
              lambda e: e[addr] and not e[full] and (e[v0] or e[v1]))
        table(top, 'u0_ddr64_wrapper_i_653', "16'h000E", wiring, [addr, full, v0, v1],
              lambda e: not e[addr] and not e[full] and (e[v0] or e[v1]))
        bridge_key, _, bridge_pins = top.instance('u_AI_Mate_top/U0_ddr2hp_itcn')
        require(bridge_pins['ddr_rd_itf__arvalid'] == 'U0_ddr2hp_itcn_i_3_n_0', 'PS split destination changed')
        excerpt(EDIF, top.nets[top.by_pin[bridge_key, 'ddr_rd_itf__arvalid']]['span'], 'PS split reaches HC bridge')
        carry, cp = inspect(top, 's_data_reg[10]_i_1')
        require(carry['ref'] == 'CARRY4' and cp['CI'] == cp['CYINIT'] == '<const0>'
                and cp['(member DI 3)'] == 'pl_araddr[0]'
                and cp['(member O 3)'] == 'u_AI_Mate_top/ai_dma_rd\\.araddr[6]', 'raw bit0 to converted bit6 changed')
        table(top, 'u_ai_io/s_data[10]_i_5', "4'h6",
              {'I0': 'pl_araddr[0]', 'I1': 'u_AI_Mate_top/vma_offset[6]'},
              ['pl_araddr[0]', 'u_AI_Mate_top/vma_offset[6]'],
              lambda e: e['pl_araddr[0]'] ^ e['u_AI_Mate_top/vma_offset[6]'])
        require(cp['(member S 3)'] == 'u_ai_io/s_data[10]_i_5_n_0', 'address carry XOR connection changed')
        review['checks'].append({'name': 'raw_address_scale', 'passed': True,
                                'fact': 'raw bit0 enters converted bit6 through offset adder; 64B scale evidence',
                                'limitation': 'not a CPU byte pointer or physical address mapping; VMA value unobserved'})
        for prefix, handshake in [('ar', 'ar'), ('r', 'r')]:
            q0, q1 = f'{prefix}_dmux[0]', f'{prefix}_dmux[1]'
            valid, ready = f'debug_m_ddr_rd_itf_{handshake}valid', f'debug_m_ddr_rd_itf_{handshake}ready'
            table(mux, f'{prefix}_dmux[0]_i_1', "16'h7F40",
                  {'I0': q0, 'I1': valid, 'I2': ready, 'I3': q0}, [q0, valid, ready],
                  lambda e, q0=q0, valid=valid, ready=ready: e[q0] ^ (e[valid] and e[ready]))
            table(mux, f'{prefix}_dmux[1]_i_1', "32'h6FFF6000",
                  {'I0': q0, 'I1': q1, 'I2': valid, 'I3': ready, 'I4': q1}, [q0, q1, valid, ready],
                  lambda e, q0=q0, q1=q1, valid=valid, ready=ready: e[q1] ^ (e[q0] and e[valid] and e[ready]))
            for bit in range(2):
                reg, pins = inspect(mux, f'{prefix}_dmux_reg[{bit}]')
                require(reg['ref'] == 'FDRE' and reg['init'] == "1'b0" and pins['C'] == 'clk'
                        and pins['R'] == 'rst' and pins['CE'] == '<const1>'
                        and pins['D'] == f'{prefix}_dmux[{bit}]_i_1_n_0'
                        and pins['Q'] == f'{prefix}_dmux[{bit}]', 'round-robin state connection changed')
        for lane in range(4):
            q0, q1, valid = 'ar_dmux[0]', 'ar_dmux[1]', 'debug_m_ddr_rd_itf_arvalid'
            wires = {'I0': q1, 'I1': valid, 'I2': q0} if lane == 0 else {'I0': q0, 'I1': q1, 'I2': valid}
            table(mux, f'U{lane}_ar_axi_fifo_i_1', ["8'h04", "8'h20", "8'h40", "8'h80"][lane],
                  wires, [q0, q1, valid], lambda e, lane=lane: e[valid] and e[q0] + 2 * e[q1] == lane)
            fifo_key, _, fifo_pins = mux.instance(f'U{lane}_ar_axi_fifo')
            expected = f'U{lane}_ar_axi_fifo_i_1_n_0' if lane < 2 else f'ss{lane}_ddr_rd_itf\\.arvalid'
            require(fifo_pins['m_valid'] == expected, 'lane decoder does not feed expected FIFO')
            excerpt(EDIF, mux.nets[mux.by_pin[fifo_key, 'm_valid']]['span'], f'AR decoder feeds lane {lane} FIFO')
        q0, q1 = 'r_dmux[0]', 'r_dmux[1]'
        data = [f'ss{i}_ddr_rd_itf\\.rdata[0]' for i in range(4)]
        table(mux, 'm_ddr_rd_itf\\.rdata[0]_INST_0', "64'hAFA0CFCFAFA0C0C0",
              {'I4': q0, 'I2': q1, 'I5': data[0], 'I3': data[1], 'I1': data[2], 'I0': data[3]},
              [q0, q1] + data, lambda e: e[data[e[q0] + 2 * e[q1]]])
        q0, q1 = 'ar_dmux[0]', 'ar_dmux[1]'
        ready = [f'ss{i}_ddr_rd_itf\\.arready' for i in range(4)]
        table(mux, 'm_ddr_rd_itf\\.arready_INST_0', "64'hBFBCB3B08F8C8380",
              {'I1': q0, 'I2': q1, 'I3': ready[0], 'I4': ready[1], 'I5': ready[2], 'I0': ready[3]},
              [q0, q1] + ready, lambda e: e[ready[e[q0] + 2 * e[q1]]])
        ps = sources[PS]
        connections = [('S00_AXI_araddr', 'S_AXI_HP2_0_1_ARADDR'),
                       ('S01_AXI_araddr', 'S_AXI_HP2_1_1_ARADDR')]
        connections += [(f'S_AXI_HP{lane}_ARADDR', f'S_AXI_HP{lane}_0_1_ARADDR') for lane in (0, 1, 3)]
        connections += [('S_AXI_HP2_ARADDR', 'axi_interconnect_4_M00_AXI_ARADDR')]
        for port, signal in connections:
            hits = list(re.finditer(r'\.' + re.escape(port) + r'\(' + re.escape(signal) + r'\)', ps))
            require(len(hits) == 1, f'unique generated PS connection required: {port}/{signal}')
            pos = hits[0].start()
            start = ps.rfind('\n', 0, pos) + 1
            end = ps.find('\n', pos) + 1
            excerpt(PS, (start, end), f'generated PS connection: {port} -> {signal}')
        review['checks'].append({'name': 'generated_PS_HP_connections', 'passed': True,
                                'fact': 'HP2 has separate HC S00 and external S01 inputs; HP0/1/3 direct',
                                'limitation': 'connection evidence, not crossbar functional or board acceptance'})
        review['checks'].append({'name': 'four_lane_request_and_return_order', 'passed': True,
                                'fact': 'AR and R have independent reset-zero counters; each increments mod4 on its own handshake',
                                'limitation': 'no reachable-state/equivalence proof; counts alone do not identify a failed HP lane'})
        review['passed'] = True
    except Exception as error:
        review['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        review['elapsed_seconds'] = round(time.monotonic() - started, 3)
        review['truth_table_count'] = len(review['truth_tables'])
        review['truth_table_rows'] = sum(len(t['rows']) for t in review['truth_tables'])
        review['excerpt_bytes'] = excerpt_bytes
        review['not_established'] = ['actual VMA/addr_offset values', 'raw sample to CPU physical mapping',
                                     'actual failed HC lane', 'DDR/PS/HDMI root cause',
                                     'complete state-machine or implementation equivalence']
        (out / 'review-driver.py').write_bytes(Path(__file__).read_bytes())
        (out / 'review.json').write_text(json.dumps(review, indent=2), encoding='utf-8')
        manifest = [{'path': p.name, 'bytes': p.stat().st_size, 'SHA256': sha(p.read_bytes())}
                    for p in sorted(out.iterdir()) if p.is_file()]
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: review[k] for k in ('passed', 'elapsed_seconds', 'truth_table_count',
                                           'truth_table_rows', 'excerpt_bytes')}))
    if not review['passed']:
        print(json.dumps(review.get('error')), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
