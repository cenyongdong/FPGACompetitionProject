"""Offline causal recovery candidate; original live results remain unchanged."""
import argparse
from collections import Counter
import json
from pathlib import Path

from analyze_node_stability import replay_events


def evaluate(pcap,profile):
    _,windows,state=replay_events(pcap,profile,retry_startup=True)
    valid=[w for w in windows if w.valid]
    ids=[o.index for w in valid for o in w.observations]
    if len(ids)!=len(set(ids)):raise ValueError('Recovery reused a selected event')
    original=json.loads((pcap.parent/'summary.json').read_text())
    original_windows=json.loads((pcap.parent/'windows.json').read_text())
    def identity(w):return (w.segment,w.start_slot,tuple(o.index if o else -1 for o in w.observations))
    old_ids={(w['segment'],w['start_slot'],tuple(w['original_event_indices'])) for w in original_windows if w['valid']}
    new_ids={identity(w) for w in valid}
    # A successful original lock must not be retuned or have its frames changed.
    preserved=old_ids.issubset(new_ids)
    if not preserved:raise ValueError('Recovery changed an already accepted window')
    return dict(source=str(pcap),live_candidate_tested=False,
        original_live=dict(valid_windows=original['valid_windows'],windows=original['windows']),
        offline_candidate=dict(valid_windows=len(valid),windows=len(windows),valid_fraction=len(valid)/len(windows) if windows else None,
            rejected_reasons=dict(Counter(w.reason for w in windows if not w.valid)),
            startup=state['startup'],existing_accepted_windows_preserved=preserved,
            first_selected_original_event=ids[0] if ids else None),
        policy=dict(retry_startup=True,failed_prefix_reused=False,warmup_us=1000000,
            min_observations=120,min_concentration=.75,tolerance_fraction=.25,
            phase_changes_after_successful_lock=False,period_hz=300,interpolation=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('captures',type=Path,nargs='+')
    a=p.parse_args();profile=json.loads(a.profile.read_text())
    rows=[evaluate(pcap,profile) for pcap in a.captures]
    a.output.write_text(json.dumps(dict(offline_only=True,default_live_policy_changed=False,results=rows),indent=2),encoding='utf-8')
    for row in rows:print(json.dumps(row))
