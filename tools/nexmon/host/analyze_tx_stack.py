"""Audit Pktmon transmit traversal using the sender's payload identity.

This measures Windows stack observation points, not RF transmission or delivery.
No 802.11 sequence field is used as a packet identity. Run with one or more case
directories containing stack.txt and sender.json; structured results go to stdout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import struct


MAGIC = b"CSI300V1"
STAMP = re.compile(r"::(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\.(\d+)")
EVENT = re.compile(r"(?:事件|Event)\s*:\s*(\d+)")
HEX = re.compile(r"^\s*0x([0-9a-fA-F]+):\s*(.*)$")


def timestamp_ns(line):
    match = STAMP.search(line)
    if not match:
        return None
    # A naive civil-time axis avoids inventing a timezone/QPC calibration.
    seconds = int((datetime.strptime(match[1], "%Y-%m-%d %H:%M:%S") -
                   datetime(1970, 1, 1)).total_seconds())
    return seconds * 1_000_000_000 + int((match[2] + "000000000")[:9])


def field(line, aliases, number=False):
    match = re.search(r"(?:" + aliases + r")\s*(?::|=)?\s*" +
                      (r"(\d+)" if number else r"([^,，\s]+)"), line)
    return (int(match[1]) if number else match[1]) if match else None


def blocks(text):
    header, lines = None, []
    for line in text.splitlines():
        if line.startswith("[") and "::" in line:
            if header is not None:
                yield header, lines
            header, lines = line, []
        else:
            lines.append(line)
    if header is not None:
        yield header, lines


def snapshot(lines):
    result = bytearray()
    for line in lines:
        match = HEX.match(line)
        if not match:
            continue
        if int(match[1], 16) != len(result):
            return None
        # The converter may append an ASCII column after the byte groups.
        groups = re.match(r"((?:[0-9a-fA-F]{4}(?:\s+|$))+|"
                          r"(?:[0-9a-fA-F]{2}(?:\s+|$))+)", match[2])
        if not groups:
            return None
        result.extend(bytes.fromhex(groups[1]))
    return bytes(result)


def stats_ms(values_ns):
    values = sorted(values_ns)
    if not values:
        return {"count": 0}
    def quantile(q):
        pos = (len(values) - 1) * q
        low = int(pos)
        return (values[low] + (values[min(low + 1, len(values)-1)] -
                              values[low]) * (pos-low)) / 1e6
    return {"count": len(values), "min": values[0]/1e6,
            "p50": quantile(.5), "p95": quantile(.95),
            "p99": quantile(.99), "max": values[-1]/1e6}


def ranges(values):
    output = []
    for value in sorted(set(values)):
        if output and value == output[-1][1] + 1:
            output[-1][1] = value
        else:
            output.append([value, value])
    return output


def analyze(case):
    case = Path(case)
    sender = json.loads((case / "sender.json").read_text(encoding="utf-8-sig"))
    job_id = bytes.fromhex(sender["id"].replace("-", ""))
    if len(job_id) != 16:
        raise ValueError("sender.id must encode 16 bytes")
    columns = dict((name, i) for i, name in enumerate(sender["columns"]))
    rows = {int(row[columns["slot"]]): row for row in sender["sends"]}
    expected = set(rows)
    raw = (case / "stack.txt").read_bytes()
    text = raw.decode("utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff")
                      else "utf-8-sig", errors="replace")
    counts = Counter()
    events = []
    components = {}
    rundown = []
    lost = {key: [int(x) for x in re.findall(key + r"\s*:\s*(\d+)", text)]
            for key in ("EventsLost", "BuffersLost")}
    bounds = []
    for header, lines in blocks(text):
        stamp = timestamp_ns(header)
        if stamp is not None:
            bounds.append(stamp)
        match = EVENT.search(header)
        if not match or "Microsoft-Windows-PktMon" not in header:
            continue
        number = int(match[1])
        counts["event_" + str(number)] += 1
        component = field(header, "组件|Component", True)
        if number == 20 and component is not None:
            name = re.search(r"(?:名称|Name)\s*(?::|=)?\s*(.*)$", header)
            components[component] = name[1].strip() if name else None
        if number in (80, 90) and component is not None:
            outgoing = re.search(r"(?:传出方向|OutgoingDirection)\s*=\s*Tx\b(.*)$", header)
            if outgoing:
                tail = outgoing[1]
                packets = field(tail, "传出数据包|OutgoingPackets", True)
                byte_count = field(tail, "传出字节|OutgoingBytes", True)
                if packets is not None:
                    rundown.append({"component": component,
                                    "counter": "drop" if number == 80 else "flow",
                                    "edge": field(header, "边缘 ID|Edge ID|EdgeId", True),
                                    "tx_packets": packets, "tx_bytes": byte_count})
        if number != 160:
            continue
        if field(header, "方向|Direction") != "Tx":
            counts["non_tx_payload_events"] += 1
            continue
        packet = snapshot(lines)
        if packet is None:
            counts["malformed_hex_snapshot"] += 1
            continue
        offset = packet.find(MAGIC)
        if offset < 0:
            counts["without_sender_magic"] += 1
            continue
        if len(packet) < offset + 48:
            counts["truncated_identity"] += 1
            continue
        if packet[offset+32:offset+48] != job_id:
            counts["other_job_uuid"] += 1
            continue
        slot, before, target = struct.unpack_from("<QQQ", packet, offset+8)
        if slot not in rows:
            counts["slot_absent_from_sender"] += 1
            continue
        row = rows[slot]
        if (before != row[columns["before_send_ns"]] or
                target != row[columns["target_ns"]]):
            counts["payload_ledger_mismatch"] += 1
            continue
        edge = field(header, "边缘|Edge", True)
        kind = field(header, "类型|Type")
        if None in (stamp, component, edge, kind):
            counts["missing_event_metadata"] += 1
            continue
        events.append({"slot": slot, "time_ns": stamp, "component": component,
                       "edge": edge, "type": kind,
                       "original_size": field(header, "OriginalSize", True)})
    by_slot, by_edge = defaultdict(list), defaultdict(list)
    for event in events:
        by_slot[event["slot"]].append(event)
        by_edge[(event["component"], event["edge"], event["type"])].append(event)
    origin = min((x["time_ns"] for x in events), default=0)
    period = 1e9 / sender["requested_hz"]
    coverage = []
    coverage_sets = []
    coverage_ids = {}
    def coverage_id(seen):
        key = tuple(sorted(seen))
        if key not in coverage_ids:
            coverage_ids[key] = len(coverage_sets)
            coverage_sets.append({"id": coverage_ids[key], "unique_slots": len(key),
                                  "slot_ranges": ranges(seen),
                                  "missing_sender_slot_ranges": ranges(expected-seen)})
        return coverage_ids[key]
    for (component, edge, kind), observations in sorted(by_edge.items()):
        first = {}
        for event in sorted(observations, key=lambda x: x["time_ns"]):
            first.setdefault(event["slot"], event["time_ns"])
        ordered = sorted(first.items(), key=lambda pair: pair[1])
        intervals = [b[1]-a[1] for a,b in zip(ordered, ordered[1:])]
        adjacent = [b[1]-a[1] for a,b in zip(ordered, ordered[1:]) if b[0] == a[0]+1]
        seen = set(first)
        coverage.append({"component": component, "name": components.get(component),
                         "edge": edge, "direction": "Tx", "type": kind,
                         "events": len(observations), "unique_slots": len(seen),
                         "first_slot": min(seen), "last_slot": max(seen),
                         "slot_coverage_id": coverage_id(seen),
                         "unobserved_tail_after_max_slot": len([s for s in expected if s > max(seen)]),
                         "first_event_elapsed_ms": (ordered[0][1]-origin)/1e6,
                         "last_event_elapsed_ms": (ordered[-1][1]-origin)/1e6,
                         "original_sizes": dict(Counter(x["original_size"] for x in observations)),
                         "interval_ms": stats_ms(intervals),
                         "consecutive_slot_interval_ms": stats_ms(adjacent),
                         "interval_below_quarter_period": sum(x < period/4 for x in intervals),
                         "interval_above_1_75_period": sum(x > period*1.75 for x in intervals),
                         "chronological_slot_reversals": sum(b[0] < a[0] for a,b in zip(ordered, ordered[1:]))})
    spans = [(slot, max(x["time_ns"] for x in observations) -
              min(x["time_ns"] for x in observations), len(observations))
             for slot, observations in by_slot.items()]
    observed = set(by_slot)
    return {"schema": 1, "case": str(case), "sender_id": sender["id"],
            "sender_calls": len(rows), "requested_hz": sender["requested_hz"],
            "validated_payload_events": len(events), "observed_slots": len(observed),
            "missing_sender_slot_ranges": ranges(expected-observed),
            "parser_counts": dict(counts), "etw_loss_counters": lost,
            "trace_bounds_ns_civil": [min(bounds), max(bounds)] if bounds else None,
            "coverage_sets": coverage_sets,
            "per_component_edge": coverage,
            "rundown_tx_counters": [item for item in rundown
                                    if item["component"] in {key[0] for key in by_edge}],
            "observations_per_slot": dict(Counter(len(x) for x in by_slot.values())),
            "earliest_to_latest_stack_observation_ms": stats_ms(span for _,span,_ in spans),
            "largest_stack_spans": [{"slot": s, "span_ms": ns/1e6, "observations": n}
                                    for s,ns,n in sorted(spans, key=lambda x: x[1], reverse=True)[:10]],
            "limitations": ["Payload magic, UUID, slot and embedded QPC times match sender ledger; NDIS SeqCtl is unused.",
                            "Stack observation span excludes time after the last observed component, firmware queues and RF transmission.",
                            "Missing component observations are evidence of absent trace traversal, not proof of packet loss at that component.",
                            "Zero ETW loss counters do not establish that a bounded in-memory trace retained all earlier history.",
                            "Rundown counters cover the capture filter, not the UUID-validated subset.",
                            "Civil ETW timestamps are used only for within-trace differences; no absolute ETW/QPC clock calibration is inferred."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps([analyze(case) for case in args.cases], indent=2, ensure_ascii=False))
