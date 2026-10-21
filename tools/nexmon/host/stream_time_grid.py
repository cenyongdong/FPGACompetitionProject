"""Causal single-node time adapter; emits references to real native64 events.

Only the startup prefix estimates phase. The 300 Hz period and phase then stay
fixed until an explicitly supplied clock-segment reset. This is independent of
model preprocessing and never creates board/model packets.
"""
from dataclasses import dataclass
from collections import deque

import numpy as np

HZ = 300
SCALE = 1_000_000  # coordinates are hardware microseconds multiplied by HZ
HALF = SCALE // 2


def estimate_phase(times_us):
    """Circular centre followed by a robust median, using this prefix only."""
    t = np.asarray(times_us, dtype='i8')
    if len(t) < 2 or np.any(np.diff(t) <= 0):
        raise ValueError('Phase estimation needs increasing observations')
    residues = ((t - t[0]) * HZ) % SCALE
    z = np.mean(np.exp(2j * np.pi * residues / SCALE))
    seed = float(np.angle(z) * SCALE / (2 * np.pi))
    offsets = (residues - seed + HALF) % SCALE - HALF
    relative = int(round(seed + float(np.median(offsets)))) % SCALE
    return dict(phase_scaled=(int(t[0]) * HZ + relative) % SCALE,
                concentration=float(abs(z)), observations=len(t),
                span_us=int(t[-1] - t[0]))


@dataclass
class Observation:
    index: int
    time_us: int
    payload: object = None
    original_words: object = None


@dataclass
class Window:
    segment: int
    start_slot: int
    observations: tuple
    target_scaled: tuple
    close_time_us: int
    valid: bool
    reason: str
    interval_gate: bool


class TimeGridStream:
    """Bounded prefix + one cell + at most 20 slots; no completed-window queue.

    feed returns windows finalized by the current hardware-time watermark.
    The caller consumes results immediately. An idle/EOF tail is discarded:
    absence of future packets is not proof of later hardware time. Startup
    cells are discarded and are never reused for evaluation.
    """
    def __init__(self, warmup_us=1_000_000, tolerance_fraction=.25,
                 min_observations=120, min_concentration=.75, max_warmup_events=1024):
        if (warmup_us <= 0 or not 0 < tolerance_fraction <= .5 or
                min_observations < 2 or max_warmup_events < min_observations or
                not 0 <= min_concentration <= 1):
            raise ValueError('Invalid fixed adapter configuration')
        self.warmup_us = warmup_us
        self.tolerance_scaled = tolerance_fraction * SCALE
        self.min_observations = min_observations
        self.min_concentration = min_concentration
        self.max_warmup_events = max_warmup_events
        self.segment = -1
        self.total_windows = self.valid_windows = self.rejected_windows = 0
        self.startup_records = deque(maxlen=64)
        self.max_buffered_observations = 0
        self.reset(0)

    def reset(self, segment):
        self.segment = int(segment)
        self.prefix = []
        self.previous_time = None
        self.previous_index = None
        self.calibration = None
        self.failed = False
        self.slot = None
        self.first_slot = None
        self.best = None
        self.block = []
        self.targets = []

    def _finish_slot(self, close_us):
        centre = self.calibration['phase_scaled'] + self.slot * SCALE
        self.block.append(self.best)
        self.targets.append(centre)
        self.best = None
        self.slot += 1
        if len(self.block) < 20:
            return None
        present = all(o is not None for o in self.block)
        point_ok = present and all(abs(o.time_us * HZ - target) <= self.tolerance_scaled
                                  for o, target in zip(self.block, self.targets))
        interval_ok = point_ok and all(abs((b.time_us-a.time_us)*HZ-SCALE) <= self.tolerance_scaled
                                      for a, b in zip(self.block, self.block[1:]))
        reason = '' if point_ok else ('missing_cell' if not present else 'point_error')
        w = Window(self.segment, self.slot-20-self.first_slot, tuple(self.block),
                   tuple(self.targets), int(close_us), bool(point_ok), reason, bool(interval_ok))
        self.block, self.targets = [], []
        self.total_windows += 1
        self.valid_windows += int(point_ok)
        self.rejected_windows += int(not point_ok)
        return w

    def feed(self, time_us, index, payload=None, original_words=None):
        time_us, index = int(time_us), int(index)
        if self.previous_time is not None and (time_us <= self.previous_time or index <= self.previous_index):
            raise ValueError('Non-increasing event/time: caller must reset discontinuous segments')
        if self.previous_time is not None and time_us-self.previous_time >= 32768:
            raise ValueError('Clock gap exceeds low16 continuity guard: caller must reset')
        self.previous_time, self.previous_index = time_us, index
        if self.failed:
            return []
        if self.calibration is None:
            if len(self.prefix) >= self.max_warmup_events:
                self.failed = True
                self.startup_records.append(dict(segment=self.segment, locked=False, reason='startup_budget'))
                self.prefix = []
                return []
            self.prefix.append(time_us)
            self.max_buffered_observations = max(self.max_buffered_observations, len(self.prefix))
            if time_us-self.prefix[0] < self.warmup_us:
                return []
            fit = estimate_phase(self.prefix)
            fit['segment'] = self.segment
            fit['calibration_end_us'] = time_us
            fit['locked'] = (len(self.prefix) >= self.min_observations and
                             fit['concentration'] >= self.min_concentration)
            self.startup_records.append(fit)
            self.prefix = []
            if not fit['locked']:
                self.failed = True
                return []
            self.calibration = fit
            # First cell's left boundary is strictly AFTER calibration end.
            self.slot = (time_us*HZ + HALF-fit['phase_scaled']) // SCALE + 1
            self.first_slot = self.slot
            return []
        scaled = time_us * HZ
        centre = self.calibration['phase_scaled'] + self.slot * SCALE
        out = []
        while scaled >= centre + HALF:
            w = self._finish_slot(time_us)
            if w is not None:
                out.append(w)
            centre = self.calibration['phase_scaled'] + self.slot * SCALE
        if scaled >= centre-HALF:
            o = Observation(index, time_us, payload, original_words)
            if self.best is None or (abs(scaled-centre), time_us, index) < (
                    abs(self.best.time_us*HZ-centre), self.best.time_us, self.best.index):
                self.best = o
        self.max_buffered_observations = max(self.max_buffered_observations,
            sum(o is not None for o in self.block) + int(self.best is not None))
        return out

    def finish(self):
        """Report and discard unfinalized tail, without padding or time guessing."""
        tail = dict(segment=self.segment, startup_pending=len(self.prefix),
                    complete_cells_in_partial_window=len(self.block), open_cell=self.best is not None)
        self.prefix = []
        self.block, self.targets, self.best = [], [], None
        return tail
