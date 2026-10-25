"""Pure same-boot conservation gate; no hardware access or input mutation."""

KNOWN = {58, 59, 61}
ALLOWED = KNOWN | {92, 93, 95}
CHANNELS = ("PS", "S01", "HC2")
EPOCH_CHANNELS = ("HC0", "HC1", "HC2", "HC3", "PS", "S01")
WRITE_COUNTS = ("legacy_AW", "legacy_W", "legacy_B", "PS_AW", "PS_W", "PS_B")


def _need(ok, why):
    if not ok:
        raise ValueError(why)


def _uint(value, name, bits=64):
    _need(type(value) is int and 0 <= value < 1 << bits, name + " invalid/missing")
    return value


def _level(record, name):
    value = record[name]
    _need(type(value) in (bool, int) and value in (0, 1), name + " is not a pin level")
    return bool(value)


def _native(protocol, consumption_underflow=False):
    _need(protocol["valid"] is True and protocol["published"] is True and protocol["fired"] is True,
          "Native first-error evidence incomplete")
    _need(protocol.get("checker_capacity_exceeded", False) is False, "Checker capacity exceeded")
    flags = protocol["live_flags"]
    _need(all(flags[name] is True for name in
              ("PS_HP2_resetn", "PC_system_resetn", "PC_checker_ready", "PC_seen_reset_low")),
          "Native checker reset/ready contract incomplete")
    witness = protocol["first_indication"]
    _need(witness["published"] is True, "Native first indication missing")
    words = witness["status_words"]
    _need(len(words) == 5 and sum(_uint(w, "native word", 32) << (32 * i)
                                 for i, w in enumerate(words)) == witness["status"],
          "Native indication words/status differ")
    rows = protocol["rows"]
    index, count = protocol["trigger_index"], protocol["count"]
    _need(type(index) is int and 0 <= index <= 32 and len(rows) == count == 96 + index,
          "Native first-error window incomplete")
    _need(all(b["HP_cycle"] == a["HP_cycle"] + 1 for a, b in zip(rows, rows[1:])),
          "Native window not consecutive")
    _need(rows[index]["HP_cycle"] == protocol["trigger_cycle"] and
          rows[index]["PC_status"] == protocol["first_status"], "Native trigger mismatch")
    values = [witness["status"], protocol["first_status"], *[row["PC_status"] for row in rows]]
    bits = set()
    for value in values:
        value = _uint(value, "native status", 160)
        bits.update(i for i in range(160) if value >> i & 1)
    for checks in [witness.get("checks", []), protocol.get("first_checks", []),
                   protocol.get("all_checks_in_window", []),
                   (protocol.get("first_protocol_rule_in_window") or {}).get("checks", [])]:
        bits.update(_uint(c["bit"], "native check bit", 8) for c in checks)
    # Frozen startup history is never granted the consumption-only exception.
    _need(bool(bits & KNOWN) and bits <= ALLOWED,
          "Missing known rule or unexpected historical checks: " + str(sorted(bits)))
    if "live_status" in protocol:
        live = _uint(protocol["live_status"], "live native status", 160)
        bits.update(i for i in range(160) if live >> i & 1)
    allowed = ALLOWED | ({79} if consumption_underflow else set())
    _need(bits <= allowed, "Unexpected live native checks: " + str(sorted(bits)))
    return bits


def evaluate(before, after, consume_trace, protocol_before, protocol_after):
    """Return eligible/reasons plus raw deltas; eligible is diagnostic admission only."""
    out = dict(eligible=False, reasons=[], boot_id=None, discard_beats=None,
               delta={}, buffered_before=None, buffered_after=None,
               protocol_history_preserved=False, functional_recovery_proved=False)
    try:
        identity = before["boot_id"]
        out["boot_id"] = identity
        _need(isinstance(identity, str) and identity and all(x["boot_id"] == identity for x in
              (after, consume_trace, protocol_before, protocol_after)), "Same-boot identities differ")
        for label, capture in (("before", before), ("after", after)):
            _need(capture["valid"] is True and capture["overflow"] is False,
                  label + " capture invalid/overflowed")
            _need(all(capture[key] == 0 for key in ("SDK", "DMA", "HDMI_START")),
                  label + " already included functional traffic")
            levels = capture["levels"]
            _need(_level(levels, "PS_HP2_resetn") and _level(levels, "PL_HP2_resetn") and
                  not _level(levels, "HP_reset"), label + " reset not released")
            _need(not any(_level(levels, channel + "_ARVALID") for channel in CHANNELS),
                  label + " contains current ARVALID")
            _need(not _level(levels, "HC2_RVALID"), label + " has a return on HC2")
            _need(capture["first_AR_HP_cycle"] is None, label + " historical AR exists")
            _uint(capture["HP_cycle"], label + " HP_cycle")
            for channel in ("PS", "S01"):
                c = capture["counts_lifetime"][channel]
                for key in ("AR", "R"):
                    _uint(c[key], label + "." + channel + "." + key)
                _need(c["AR"] == 0, label + " contains cumulative AR")
            _need(all(_uint(capture["counts_lifetime"]["writes"][key], key) == 0 for key in WRITE_COUNTS),
                  label + " contains cumulative writes")
            for channel in EPOCH_CHANNELS:
                c, p = capture["counts_epoch"][channel], capture["pins"][channel]
                for key in ("AR", "R", "RLAST", "non_OKAY", "ARVALID_cycles", "RVALID_cycles", "expected_R"):
                    _uint(c[key], label + " epoch " + channel + "." + key, 32)
                _need(c["AR"] == c["ARVALID_cycles"] == c["expected_R"] == c["non_OKAY"] == 0 and
                      not _level(p, "ARVALID"), label + " epoch request/non-OKAY")
                if channel.startswith("HC"):
                    _need(c["R"] == c["RLAST"] == c["RVALID_cycles"] == 0 and not _level(p, "RVALID"),
                          label + " AI epoch return")
                if channel in ("PS", "S01") and _level(p, "RVALID"):
                    _need(p["RID"] == (0x20 if channel == "PS" else 0) and p["RRESP"] == 0,
                          label + " pending ID/response differs")
        _need(_uint(after["observer_generation"], "after monitor generation", 32) ==
              _uint(before["observer_generation"], "before monitor generation", 32) + 2 and
              before["observer_generation"] % 2 == 0, "Not one fresh complete monitor epoch")
        first_r = _uint(before["first_RVALID_HP_cycle"], "first RVALID")
        _need(first_r == after["first_RVALID_HP_cycle"] and first_r <= before["HP_cycle"],
              "Original first-RVALID history changed/missing")
        _need(_level(before["levels"], "PS_RVALID") and _level(before["levels"], "S01_RVALID") and
              not _level(before["pins"]["S01"], "RREADY") and
              not any(_level(after["levels"], channel + "_RVALID") for channel in CHANNELS),
              "Pending seed absent or returns still present afterwards")
        bctrl, actrl = before["control"], after["control"]
        base = _uint(bctrl["request"], "before request")
        _need(bctrl["response"] == base and bctrl["arm_used"] is False and
              bctrl["arm_issued"] is False and bctrl["rearm_used"] is False and
              bctrl["rearm_issued"] is False and bctrl["error"] is False,
              "ARM was already used/pending/failed before consume")
        _need(actrl["request"] == actrl["response"] == base + 2 and
              actrl["arm_request"] == base + 1 and actrl["snapshot_request"] == base + 2 and
              actrl["commands"] == [{"opcode": 0x434f4e53, "request": base+1},
                                    {"opcode": 0x534e4150, "request": base+2}] and
              actrl["arm_used"] is True and actrl["arm_issued"] is True and
              actrl["rearm_used"] is False and actrl["rearm_issued"] is False and actrl["error"] is False,
              "Not exactly one acknowledged CONS followed by one SNAP")
        bd, ad = before["drain"], after["drain"]
        _need(bd["state"] == 0 and bd["beats"] == bd["HP_cycles"] == 0,
              "Drain was not untouched WAIT before ARM")
        for d in (bd, ad):
            _need(all(d[key] is False for key in ("saw_RRESP_error", "bad_ID", "late_RVALID")),
                  "Drain error/bad-ID/late return")
        beats = _uint(ad["beats"], "drain beats")
        out["discard_beats"] = beats
        _need(ad["state"] == 2 and 0 < beats < 256 and 64 <= ad["HP_cycles"] < 4096 and
              ad["saw_RLAST"] is True, "Drain did not reach bounded nonzero safe terminal")
        delta = {}
        for channel in ("PS", "S01"):
            delta[channel] = {}
            for key in ("AR", "R"):
                b, a = before["counts_lifetime"][channel][key], after["counts_lifetime"][channel][key]
                _need(a >= b, "Counter decreased/reset/wrapped: " + channel + "." + key)
                delta[channel][key] = a - b
                _need(delta[channel][key] == after["counts_epoch"][channel][key],
                      "Current monitor epoch differs from lifetime delta: " + channel + "." + key)
        out["delta"] = delta
        buffered_before = before["counts_lifetime"]["PS"]["R"] - before["counts_lifetime"]["S01"]["R"]
        buffered_after = after["counts_lifetime"]["PS"]["R"] - after["counts_lifetime"]["S01"]["R"]
        out.update(buffered_before=buffered_before, buffered_after=buffered_after)
        _need(buffered_before >= 0 and buffered_after == 0 and
              delta["S01"]["R"] == beats and buffered_before + delta["PS"]["R"] == beats,
              "PS/S01 buffered-beat conservation failed")
        _need(before["counts_lifetime"]["S01"]["R"] == 0,
              "Seed was already accepted at S01")
        # Native boot witness has no cumulative RLAST/non-OKAY fields. The
        # unknown prefilled PS beats are proved through the complete S01 trace,
        # never assigned an invented baseline RLAST value.
        _need(after["counts_epoch"]["S01"]["RLAST"] == 1,
              "Complete S01 epoch does not contain one RLAST")
        tr = consume_trace
        _need(tr["valid"] is True and tr["published"] is True and tr["overflow"] is False,
              "Consumption trace invalid/unpublished/overflowed")
        rows = tr["rows"]
        arm_raw = _uint(actrl["arm_HP_cycle_raw"], "raw ARM edge HP cycle")
        arm = _uint(actrl["first_sampled_RUN_HP_cycle_derived"], "first sampled RUN HP cycle")
        _need(arm == arm_raw+1 and tr["arm_HP_cycle"] == arm,
              "Raw ARM edge/first sampled RUN alignment differs")
        _need(isinstance(rows, list) and len(rows) == tr["count"] and len(rows) >= 2,
              "Consumption trace sample count differs")
        _need(all(_uint(b["HP_cycle"], "trace cycle") == _uint(a["HP_cycle"], "trace cycle") + 1
                  for a, b in zip(rows, rows[1:])), "Consumption trace is not consecutive")
        _need(before["HP_cycle"] < arm < after["HP_cycle"] and rows[0]["HP_cycle"] < arm <=
              rows[-1]["HP_cycle"] <= after["HP_cycle"], "ARM/snapshot/trace order differs")
        _need(next((r["HP_cycle"] for r in rows if r["drain_state"] == 1), None) == arm,
              "ARM cycle is not first sampled RUN cycle")
        first_quiet = next((r["HP_cycle"] for r in rows if r["drain_state"] == 2), None)
        _need(first_quiet is not None and first_quiet - arm == ad["HP_cycles"],
              "Trace RUN duration differs from terminal cycle count")
        accepted = {channel: [] for channel in CHANNELS}
        for row in rows:
            cycle = row["HP_cycle"]
            expected_state = 0 if cycle < arm else (1 if cycle < first_quiet else 2)
            _need(row["drain_state"] == expected_state, "Trace WAIT/RUN/QUIET order changed")
            _need(cycle >= arm or not _level(row, "S01_RREADY"),
                  "S01 was ready before explicit ARM")
            _need(_level(row, "PS_HP2_resetn") and _level(row, "PL_HP2_resetn") and
                  not _level(row, "HP_reset"), "Reset changed during consumption trace")
            _need(not any(_level(row, ch + "_ARVALID") for ch in CHANNELS), "Trace contains ARVALID")
            _need(not any(_level(row, ch + "_" + key) for ch in ("PS", "S01")
                          for key in ("AWVALID", "WVALID", "BVALID")), "Trace contains write activity")
            for ch in CHANNELS:
                valid, ready = _level(row, ch + "_RVALID"), _level(row, ch + "_RREADY")
                _level(row, ch + "_RLAST")
                if valid and ch != "HC2":
                    _need(row[ch + "_RID"] == (0x20 if ch == "PS" else 0) and row[ch + "_RRESP"] == 0,
                          "Visible return RID/RRESP differs: " + ch)
                if valid and ready:
                    _need(row["HP_cycle"] >= arm and row["drain_state"] == 1,
                          "Return accepted outside one ARM/RUN window")
                    accepted[ch].append(row)
            _need(not accepted["HC2"], "HC2 accepted discarded data")
        for ch in ("PS", "S01"):
            accepted_rows = accepted[ch]
            last_count = sum(_level(r, ch + "_RLAST") for r in accepted_rows)
            _need(len(accepted_rows) == delta[ch]["R"] and
                  last_count == after["counts_epoch"][ch]["RLAST"],
                  "Trace/current epoch differs: " + ch)
            _need(last_count <= 1 and (last_count == 0 or _level(accepted_rows[-1], ch+"_RLAST")),
                  "Multiple/non-final observed RLAST: " + ch)
            _need(ch == "PS" or (accepted_rows and _level(accepted_rows[-1], ch + "_RLAST") and last_count == 1),
                  "Return path lacks one final RLAST: " + ch)
        last_return = max(r["HP_cycle"] for ch in ("PS", "S01") for r in accepted[ch])
        tail = [r for r in rows if r["HP_cycle"] > last_return]
        _need(len(tail) >= 64 and rows[-1]["drain_state"] == 2 and all(
              not _level(r, ch + "_RVALID") for r in tail for ch in CHANNELS),
              "No complete empty 64-HP-cycle terminal tail")
        before_pc = _uint(protocol_before["capture_HP_cycle"], "protocol before cycle")
        after_pc = _uint(protocol_after["capture_HP_cycle"], "protocol after cycle")
        _need(before["HP_cycle"] <= before_pc == bctrl["capture_HP_cycle"] < arm_raw and
              arm_raw + ad["HP_cycles"] <= after_pc == actrl["capture_HP_cycle"] <= after["HP_cycle"] and
              after_pc >= first_quiet and
              before["control_capture_HP_cycle"] == before_pc and after["control_capture_HP_cycle"] == after_pc,
              "Separate control SNAP / observer FREEZE ordering differs")
        _need(protocol_before["live_status"] == bctrl["full_PC_status"] and
              protocol_after["live_status"] == actrl["full_PC_status"] and
              bctrl["PC_system_resetn"] and bctrl["PC_checker_ready"] and
              actrl["PC_system_resetn"] and actrl["PC_checker_ready"],
              "Native live status is not the acknowledged control snapshot")
        before_bits, after_bits = _native(protocol_before), _native(protocol_after, consumption_underflow=True)
        _need(before_bits <= after_bits, "Native history bits disappeared")
        for key in ("first_indication", "first_status", "trigger_cycle", "trigger_index", "count", "rows"):
            _need(protocol_before[key] == protocol_after[key], "Frozen native history changed: " + key)
        out.update(eligible=True, reasons=["Same-boot nonzero consume conserved buffered and new PS returns; terminal/trace/native-history gates passed."],
                   accepted_in_trace={ch: len(accepted[ch]) for ch in CHANNELS},
                   protocol_history_preserved=True, native_check_bits=sorted(after_bits),
                   consumption_CAM_underflow_retained=79 in after_bits,
                   checker_only_rearm_required=True, fresh_functional_160_bit_gate_unchanged=True)
    except (KeyError, TypeError, IndexError, AttributeError, ValueError, StopIteration) as error:
        out["reasons"] = ["Unsafe/inconclusive consumption: " + str(error)]
    return out
