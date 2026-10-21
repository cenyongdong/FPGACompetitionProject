"""Select real first-valid CSI events on a fixed 300Hz grid, offline only.

Cells are disjoint; no observation can occupy two grid slots. An empty/outside
tolerance cell stays missing and every containing 20-slot window is rejected.
Grid phase is fixed per reliable low16-clock segment, never refitted per window.
No interpolation, model inputs, board traffic or inference are produced.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from validate_dedup import stats, write_csv

HZ = 300
SCALE = 1_000_000
SAMPLES = 20
FRACTIONS = (0.10, 0.25, 0.50)
PRIMARY = 0.25


def grid_segment(times_us, positions, original_indices, phase_offset_scaled=0):
    """Nearest in half-open disjoint cells; ties choose earliest real event.

    Integer-scaled coordinates avoid accumulating a rounded 3333us period.
    The last cell is the nearest cell of the last actual event; its centre can
    lie up to half a period beyond the last event. No further slots are inferred.
    """
    t = np.asarray(times_us, dtype='i8')
    positions = np.asarray(positions, dtype='i8')
    original_indices = np.asarray(original_indices, dtype='i8')
    if len(t) == 0 or len(t) != len(positions) or len(t) != len(original_indices):
        raise ValueError('Expected corresponding nonempty time/event arrays')
    if np.any(np.diff(t) <= 0):
        raise ValueError('Non-increasing hardware time within segment')
    if not 0 <= phase_offset_scaled < SCALE:
        raise ValueError('Phase offset must be within one fixed period')
    event_anchor = int(t[0])
    raw_cells = ((t-event_anchor)*HZ-phase_offset_scaled+SCALE//2) // SCALE
    first_cell = int(raw_cells[0])
    cells = raw_cells-first_cell
    anchor = event_anchor+(phase_offset_scaled+first_cell*SCALE)/HZ
    nslots = int(cells[-1])+1
    if nslots > 100000:
        raise ValueError('Grid exceeds bounded offline capture budget')
    selected = np.full(nslots,-1,dtype='i8')
    errors = np.full(nslots,np.nan,dtype='f8')
    counts = np.zeros(nslots,dtype='i8')
    for local, slot in enumerate(cells):
        slot = int(slot)
        error = int((t[local]-event_anchor)*HZ-phase_offset_scaled-int(raw_cells[local])*SCALE)
        counts[slot] += 1
        old = int(selected[slot])
        if old == -1 or (abs(error),int(t[local]),int(positions[local])) < (
                abs(int(errors[slot])),int(t[old]),int(positions[old])):
            selected[slot], errors[slot] = local, error
    found = selected >= 0
    mapped_positions = np.full(nslots,-1,dtype='i8')
    mapped_originals = np.full(nslots,-1,dtype='i8')
    actual = np.full(nslots,np.nan,dtype='f8')
    mapped_positions[found] = positions[selected[found]]
    mapped_originals[found] = original_indices[selected[found]]
    actual[found] = t[selected[found]]
    return dict(anchor_us=anchor,slots=nslots,positions=mapped_positions,
                originals=mapped_originals,actual_us=actual,errors_scaled=errors,
                candidates=counts,source_events=len(t))


def available(grid, fraction):
    return (grid['positions'] >= 0) & (np.abs(grid['errors_scaled']) <= fraction*SCALE)


def window_rows(segment, grid):
    """Use a single selection for both fixed-stride and overlapping diagnostics."""
    rows = []
    masks = {f:available(grid,f) for f in FRACTIONS}
    for start in range(max(0,grid['slots']-SAMPLES+1)):
        end = start+SAMPLES
        row = dict(segment=int(segment),start_slot=start,end_slot=end-1,
                   nonoverlapping=start % SAMPLES == 0)
        for fraction in FRACTIONS:
            key = int(fraction*100)
            mask = masks[fraction][start:end]
            row[f'missing_{key}pct'] = int(np.sum(~mask))
            row[f'valid_{key}pct'] = bool(mask.all())
            # Retain the previous stage's interval-error condition separately:
            # complete grid coverage alone permits interval error up to 2*tolerance.
            interval_error = None
            if mask.all():
                actual = grid['actual_us'][start:end]
                interval_error = float(np.max(np.abs(np.diff(actual)-SCALE/HZ)))
            row[f'also_previous_interval_gate_{key}pct'] = bool(mask.all() and
                    interval_error <= fraction*SCALE/HZ)
        if row['valid_25pct']:
            actual = grid['actual_us'][start:end]
            row.update(actual_span_us=float(actual[-1]-actual[0]),
                max_point_error_us=float(np.max(np.abs(grid['errors_scaled'][start:end]))/HZ),
                max_interval_error_us=float(np.max(np.abs(np.diff(actual)-SCALE/HZ))))
        else:
            row.update(actual_span_us=None,max_point_error_us=None,max_interval_error_us=None)
        rows.append(row)
    return rows


def summarize(grid, rows, fixed_stride):
    eligible = [r for r in rows if r['nonoverlapping']] if fixed_stride else rows
    result = dict(total_windows=len(eligible))
    for fraction in FRACTIONS:
        key = int(fraction*100)
        valid = [r for r in eligible if r[f'valid_{key}pct']]
        n = len(valid)
        longest = run = 0
        longest_start = start = None
        for r in eligible:
            if r[f'valid_{key}pct']:
                if run == 0:
                    start = r['start_slot']
                run += 1
                if run > longest:
                    longest, longest_start = run, start
            else:
                run = 0
        result[f'tolerance_{key}pct'] = dict(valid_windows=n,invalid_windows=len(eligible)-n,
            valid_fraction=n/len(eligible) if eligible else None,
            also_previous_interval_gate=sum(r[f'also_previous_interval_gate_{key}pct'] for r in eligible),
            longest_consecutive_valid_windows=longest,longest_run_start_slot=longest_start)
    return result


def analyze(source, output):
    output.mkdir(parents=True,exist_ok=False)
    dedup_summary = json.loads((source/'summary.json').read_text(encoding='utf-8'))
    if not dedup_summary['offline_only'] or dedup_summary['model_ready']:
        raise ValueError('Require independent offline first-valid event export')
    with np.load(source/'retained-node-events.npz') as z:
        indices = z['original_event_indices'].astype('i8')
        segments = z['clock_segments'].astype('i8')
        times = z['segment_time_us'].astype('i8')
        shape = list(z['packed_words'].shape)
        if shape != [len(indices),3,64] or np.any(np.diff(indices) <= 0):
            raise ValueError('Unexpected node/core/FFT layout or event reordering')
    all_slots, all_windows, segment_results = [], [], []
    exported_positions, exported_indices, exported_times, exported_targets = [], [], [], []
    exported_segments, exported_starts = [], []
    used = set()
    for segment in np.unique(segments):
        positions = np.flatnonzero(segments==segment)
        g = grid_segment(times[positions],positions,indices[positions])
        masks = {f:available(g,f) for f in FRACTIONS}
        found = g['positions'] >= 0
        if len(np.unique(g['positions'][found])) != int(found.sum()):
            raise ValueError('One event assigned to multiple grid slots')
        for slot in range(g['slots']):
            p = int(g['positions'][slot])
            row = dict(segment=int(segment),slot=slot,
                target_segment_time_us=g['anchor_us']+slot*SCALE/HZ,
                nearest_retained_position=p if p>=0 else None,
                nearest_original_event=int(g['originals'][slot]) if p>=0 else None,
                actual_segment_time_us=float(g['actual_us'][slot]) if p>=0 else None,
                signed_error_us=float(g['errors_scaled'][slot]/HZ) if p>=0 else None,
                candidates_in_cell=int(g['candidates'][slot]))
            for f in FRACTIONS:
                row[f'available_{int(f*100)}pct'] = bool(masks[f][slot])
            all_slots.append(row)
        rows = window_rows(segment,g)
        all_windows.extend(rows)
        fixed = summarize(g,rows,True)
        sliding = summarize(g,rows,False)
        segment_results.append(dict(segment=int(segment),source_events=len(positions),
            first_original_event=int(indices[positions[0]]),last_original_event=int(indices[positions[-1]]),
            local_span_us=int(times[positions[-1]]-times[positions[0]]),
            grid_slots=g['slots'],empty_cells=int(np.sum(~found)),
            multi_observation_cells=int(np.sum(g['candidates']>1)),
            extra_observations_not_reused=int(sum(g['candidates'])-sum(found)),
            available_cells={str(int(f*100)):int(available(g,f).sum()) for f in FRACTIONS},
            trailing_slots_not_a_complete_fixed_window=g['slots'] % SAMPLES,
            nonoverlapping=fixed,sliding=sliding))
        for r in rows:
            if not (r['nonoverlapping'] and r['valid_25pct']):
                continue
            start = r['start_slot']; end = start+SAMPLES
            selected = g['positions'][start:end]
            if any(int(x) in used for x in selected):
                raise ValueError('Real observation reused across nonoverlapping output windows')
            used.update(map(int,selected))
            if len(selected)!=20 or np.any(selected<0) or np.any(np.diff(selected)<=0):
                raise ValueError('Missing, reused or reordered event in accepted window')
            exported_positions.append(selected)
            exported_indices.append(g['originals'][start:end])
            exported_times.append(g['actual_us'][start:end])
            exported_targets.append(g['anchor_us']+np.arange(start,end)*SCALE/HZ)
            exported_segments.append(int(segment));exported_starts.append(start)
    def totals(name):
        total=sum(r[name]['total_windows'] for r in segment_results)
        result=dict(total_windows=total)
        for fraction in FRACTIONS:
            key=f'tolerance_{int(fraction*100)}pct'
            good=sum(r[name][key]['valid_windows'] for r in segment_results)
            result[key]=dict(valid_windows=good,invalid_windows=total-good,
                valid_fraction=good/total if total else None,
                also_previous_interval_gate=sum(r[name][key]['also_previous_interval_gate'] for r in segment_results))
        return result
    longest = max(segment_results,key=lambda r:(r['local_span_us'],r['source_events']))
    primary_windows=[r for r in all_windows if r['nonoverlapping'] and r['valid_25pct']]
    write_csv(output/'grid-slots.csv',all_slots)
    write_csv(output/'windows20.csv',all_windows)
    np.savez_compressed(output/'accepted-window-indices.npz',
        retained_positions=np.asarray(exported_positions,dtype='<i8').reshape(-1,20),
        original_event_indices=np.asarray(exported_indices,dtype='<i8').reshape(-1,20),
        actual_segment_time_us=np.asarray(exported_times,dtype='<f8').reshape(-1,20),
        target_segment_time_us=np.asarray(exported_targets,dtype='<f8').reshape(-1,20),
        segments=np.asarray(exported_segments,dtype='<i8'),start_slots=np.asarray(exported_starts,dtype='<i8'))
    result=dict(schema=1,offline_only=True,model_ready=False,source_directory=str(source.resolve()),
        source_pcap_sha256=dedup_summary['source_sha256_from_capture_manifest'],
        source_retained_events=len(indices),source_packed_shape=shape,
        hardware_or_model_inference_performed=False,model_preprocessing_or_board_protocol_changed=False,
        selection_policy=dict(target_hz=HZ,period_us=SCALE/HZ,window_slots=SAMPLES,
            primary_tolerance_fraction=PRIMARY,primary_tolerance_us=PRIMARY*SCALE/HZ,
            sensitivity_tolerances_us={str(int(f*100)):f*SCALE/HZ for f in FRACTIONS},
            phase='First retained event per reliable clock segment; fixed thereafter, never refitted per window.',
            cell='Half-open nearest-grid cells, one closest actual observation per cell; ties use earlier observation.',
            edge='First cell anchored to first event; last cell is nearest-grid cell of last event. Partial fixed windows are reported but not counted complete.',
            missing='Empty/outside-tolerance cell remains missing; reject every containing window. No interpolation, reuse in another cell or temporal compression.',
            tolerance_status='Engineering diagnostics, not trained-model accuracy acceptance.',
            previous_interval_gate='Reported separately; full grid coverage does not imply the previous consecutive-interval criterion passes.'),
        clock_scope=dict(reliable_segments=len(segment_results),unresolved_boundaries=dedup_summary['clock_boundaries'],
            cross_boundary_windows='Never accepted; cannot enumerate their global-grid count with low16 timestamps.',
            global_whole_capture_valid_fraction=None,
            denominator='Complete grid windows inside reliable clock segments. Excludes unresolvable time across boundaries and partial tail windows; not a 16s global/UDP-delivery success rate.'),
        all_reliable_segments=dict(nonoverlapping=totals('nonoverlapping'),sliding=totals('sliding')),
        longest_continuous_segment=longest,segments=segment_results,
        accepted_primary_nonoverlapping_windows=len(exported_positions),
        primary_accepted_timing=dict(actual_span_us=stats([r['actual_span_us'] for r in primary_windows]),
            max_point_error_us=stats([r['max_point_error_us'] for r in primary_windows]),
            max_interval_error_us=stats([r['max_interval_error_us'] for r in primary_windows])),
        invariants=dict(no_interpolation=True,no_frame_duplication_within_or_across_grid_cells=True,
            no_frame_reuse_across_primary_nonoverlapping_windows=True,no_cross_segment_windows=True,
            selected_frames_are_original_first_valid_observations=True),
        model_contract=dedup_summary['model_contract'],
        limitations=['The longest continuous segment is determined solely by hardware-clock coverage, not by optimizing window validity. It is not an independently identified exact transmitter QPC interval.',
            'Grid coordinates are target indices; actual RF reception times and CSI words remain unchanged, so selected observations are not perfectly uniformly sampled.',
            'Background traffic can supply occupied cells; application UDP slot-to-RF identity is still unknown.',
            'Partial windows and gaps at clock discontinuities are not filled. A full-capture/global-grid valid rate cannot be proved with this metadata.',
            'Even complete temporal grids are single-node/native64 candidates, not the required three-node/30-carrier model input or pose-accuracy validation.'])
    (output/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.source,a.output)
    print(json.dumps(dict(all_reliable_segments=r['all_reliable_segments'],
        longest_continuous_segment=r['longest_continuous_segment'],
        accepted_primary_nonoverlapping_windows=r['accepted_primary_nonoverlapping_windows'],
        primary_accepted_timing=r['primary_accepted_timing'],model_ready=r['model_ready']),indent=2))
