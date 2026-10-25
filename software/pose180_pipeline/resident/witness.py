"""Read-only cross-check of the three r45 first-RVALID witnesses.

No timestamp correction, MMIO, command, retry, or admission override. The
original seed and post-consumption gates remain mandatory. A common clock
does not itself prove equal origins for separately initialized counters.
"""


def compare(before, trace, protocol):
    result = dict(consistent=False, boot_id=before.get('boot_id'),
                  snapshot_cycle=before.get('first_RVALID_HP_cycle'),
                  trace_cycle=None, protocol_edge_cycle=None,
                  trace_minus_snapshot=None, overlapping_samples=0,
                  signal_mismatches=[], issues=[], timestamp_adjustment=0)
    try:
        def need(ok, message):
            if not ok:
                raise ValueError(message)

        need(before['boot_id'] == trace['boot_id'] == protocol['boot_id'], 'Mixed boot witnesses')
        bank = trace['banks'][0]
        first = result['snapshot_cycle']
        if first is None and not bank['published'] and not protocol['published']:
            need(not protocol['fired'] and not bank.get('fired', False), 'Unpublished witness already fired')
            result.update(consistent=True, relation='no_first_return_observed')
            return result
        need(type(first) is int and 0 <= first < 2**64, 'First-event snapshot absent or invalid')
        need(bank['published'] and protocol['published'], 'A native witness is missing')
        rows = bank['rows']
        native = protocol['rows']
        need(len(rows) == bank['count'] == 128 and bank['trigger_index'] == 32, 'Incomplete first-return window')
        need(len(native) == protocol['count'] == 128, 'Incomplete protocol window')
        for sequence in (rows, native):
            need(all(b['HP_cycle'] == a['HP_cycle']+1 for a, b in zip(sequence, sequence[1:])), 'Nonconsecutive native samples')
        result['trace_cycle'] = bank['trigger_cycle']
        result['trace_minus_snapshot'] = bank['trigger_cycle'] - first
        need(rows[32]['HP_cycle'] == bank['trigger_cycle'] and not rows[31]['PS_RVALID'] and rows[32]['PS_RVALID'], 'Trace descriptor/edge differs')
        edge = next((i for i, row in enumerate(native) if row['PS_RVALID']), None)
        need(edge is not None and edge > 0 and not native[edge-1]['PS_RVALID'], 'Protocol window lacks a witnessed first edge')
        result['protocol_edge_cycle'] = native[edge]['HP_cycle']
        lookup = {row['HP_cycle']: row for row in native}
        for row in rows:
            other = lookup.get(row['HP_cycle'])
            if other is None:
                continue
            result['overlapping_samples'] += 1
            fields = ['PS_ARVALID', 'PS_ARREADY', 'PS_RVALID', 'PS_RREADY']
            if row['PS_RVALID'] and other['PS_RVALID']:
                fields += ['PS_RDATA', 'PS_RID', 'PS_RRESP', 'PS_RLAST']
            for key in fields:
                if row[key] != other[key] and len(result['signal_mismatches']) < 16:
                    result['signal_mismatches'].append(dict(cycle=row['HP_cycle'], field=key,
                                                          trace=row[key], protocol=other[key]))
        need(result['overlapping_samples'] >= 32, 'Insufficient common native coverage')
        need(not result['signal_mismatches'], 'Native sampled signals differ')
        need(first == result['trace_cycle'] == result['protocol_edge_cycle'], 'First RVALID witnesses are not exactly equal')
        result.update(consistent=True, relation='three_exact_first_event_witnesses')
    except (KeyError, IndexError, TypeError, ValueError) as error:
        result['issues'].append(str(error))
        result['relation'] = 'inconclusive_no_correction'
    return result
