"""Incremental NMD1/CSI pairing, three-core assembly, dedup and time windows.

One fixed transmitter/channel. A datagram loss or inconsistent group breaks
time continuity and resets startup calibration. No model/board protocol output.
The current tested transport is ordered router-PCAP replay, not independent
UDP sockets (which do not preserve cross-port ordering).
"""
from collections import Counter, OrderedDict

from csi_verify import parse_payload
from diagnose_metadata import decode
from stream_time_grid import TimeGridStream
from validate_dedup import finalize, CLOCK_HALF_WRAP_US, RETRY_HORIZON_US


class NodeStream:
    def __init__(self, source_mac, channel, pair_timeout_s=.020, retry_startup=False):
        self.source_mac, self.channel = source_mac.lower(), int(channel)
        self.pair_timeout_s = pair_timeout_s
        self.grid = TimeGridStream(retry_startup=retry_startup)
        self.counts = Counter()
        self.pending = None
        self.group = []
        self.key = None
        self.previous = None
        self.segment = 0
        self.local_us = 0
        self.event_index = 0
        self.recent = OrderedDict()
        self.last_packet_time = None
        self.max_recent = 0
        self.on_event = None  # optional synchronous diagnostic sink; caller owns retention
        self.on_tail = None

    def _break_clock(self, reason):
        self.counts['reset_'+reason] += 1
        tail = self.grid.finish()
        if self.on_tail is not None:
            self.on_tail(tail)
        self.segment += 1
        self.grid.reset(self.segment)
        self.previous = None
        self.local_us = 0
        self.recent.clear()

    def expire(self, arrival_time):
        """Caller must tick during silence. Host time only invalidates, never fills."""
        if self.last_packet_time is not None and arrival_time-self.last_packet_time >= CLOCK_HALF_WRAP_US/1e6:
            self._break_clock('idle')
            self.last_packet_time = None
            self.pending, self.group, self.key = None, [], None
        elif self.pending is not None and arrival_time-self.pending['time'] > self.pair_timeout_s:
            self.counts['pair_timeout'] += 1
            self.pending, self.group, self.key = None, [], None
            self._break_clock('pair_timeout')

    def _complete(self):
        event = finalize(self.event_index, self.group)
        self.event_index += 1
        self.group, self.key = [], None
        self.counts['complete_events'] += 1
        m = event.meta
        if self.previous is not None:
            host_us = (m['time']-self.previous['time'])*1e6
            delta = (m['rx_tsf16']-self.previous['rx_tsf16']) & 65535
            step = (m['event16']-self.previous['event16']) & 65535
            if not (0 < host_us < CLOCK_HALF_WRAP_US and 0 < delta < CLOCK_HALF_WRAP_US and step == 1):
                self._break_clock('clock_discontinuity')
            else:
                self.local_us += delta
        event.segment, event.time_us = self.segment, self.local_us
        self.previous = m
        now = m['time']
        while self.recent:
            _, (seen, _) = next(iter(self.recent.items()))
            if (now-seen)*1e6 <= RETRY_HORIZON_US:
                break
            self.recent.popitem(last=False)
        if not event.valid:
            event.decision = 'invalid'
        else:
            identity = (m['mac'],m['channel'],m['tid'],m['seq'])
            old = self.recent.get(identity)
            if old is not None:
                event.first_valid = old[1]
                event.decision = 'drop_retransmission' if m['retry'] else 'ambiguous_identity_reuse'
            else:
                event.decision, event.first_valid = 'keep', event.index
            self.recent[identity] = (now,event.first_valid)
            self.recent.move_to_end(identity)
            self.max_recent = max(self.max_recent,len(self.recent))
            if len(self.recent) > 1024:
                raise ValueError('Dedup horizon exceeds fixed memory budget')
        self.counts[event.decision] += 1
        if self.on_event is not None:
            self.on_event(event)
        if event.decision == 'ambiguous_identity_reuse':
            self._break_clock('ambiguous_identity')
        if event.decision != 'keep':
            return []
        # The raw event clock may remain continuous across several retries but
        # a retained-only gap can exceed the stricter grid continuity guard.
        if self.grid.previous_time is not None and event.time_us-self.grid.previous_time >= CLOCK_HALF_WRAP_US:
            self._break_clock('retained_gap')
            event.segment, event.time_us = self.segment, 0
            self.previous = m
        return self.grid.feed(event.time_us,event.index,event.words,event.original_words)

    def feed(self, arrival_time, port, payload):
        if port not in (5500,5501):
            return []
        if self.last_packet_time is not None and arrival_time < self.last_packet_time:
            raise ValueError('Arrival clock moved backwards')
        self.expire(arrival_time)
        self.last_packet_time = arrival_time
        self.counts['packets'] += 1
        if port == 5500:
            c = parse_payload(payload,64)
            if c['mac'] != self.source_mac or c['chanspec'] != self.channel:
                raise ValueError('Transmitter/channel identity changed')
            if c['chip'] != 106 or c['stream'] != 0 or c['core'] not in (0,1,2):
                raise ValueError('Radio/core/stream changed')
            if self.pending is not None:
                self.counts['unpaired_csi'] += 1
                self.group, self.key = [], None
                self._break_clock('unpaired_csi')
            self.pending = dict(mac=c['mac'],seq=c['sequence_control'],config=c['core_config_raw'],
                channel=c['chanspec'],words=c['words'],time=arrival_time)
            return []
        d=decode(payload)
        c=self.pending
        self.pending=None
        if c is None or any(d[k]!=c[k] for k in ('mac','seq','config','channel')):
            self.counts['pair_mismatch'] += 1
            self.group,self.key=[],None
            self._break_clock('pair_mismatch')
            return []
        d['time']=c['time']
        key=tuple(d[k] for k in ('mac','seq','channel','fc','qos','rx_tsf16','event16'))
        if self.group and key!=self.key:
            self.counts['incomplete_group'] += 1
            self.group=[]
            self._break_clock('incomplete_group')
        self.key=key
        if any(g[0]['config']==d['config'] for g in self.group):
            self.counts['duplicate_core'] += 1
            self.group,self.key=[],None
            self._break_clock('duplicate_core')
            return []
        self.group.append((d,c))
        return self._complete() if len(self.group)==3 else []

    def finish(self):
        tail=self.grid.finish()
        return dict(counts=dict(self.counts),clock_segment_resets=self.segment,
            last_tail=tail,trailing_unpaired_csi=self.pending is not None,
            trailing_partial_cores=len(self.group),max_recent_identities=self.max_recent,
            startup=list(self.grid.startup_records),max_grid_buffer=self.grid.max_buffered_observations)
