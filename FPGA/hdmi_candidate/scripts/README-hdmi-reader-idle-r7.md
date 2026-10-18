# HDMI reader r7 isolated full flow

`prepare_hdmi_reader_idle_reference.py` is a local file operation only. Its default
inspection verifies the original 937 sources, 41 installed files, actual miter,
canonical module-name inverse, 24 cached OOC runs and exact 25-file path whitelist.
`--prepare` requires absent W7/E7 and copies into new directories; a failure leaves
the partial tree and must not be reset/retried. It never starts Vivado or a device.

W7 is `.local/hdmi-live-20261017-r7`, E7 is
`tools/pose-v1/evidence/hdmi-live-20261017-r7`. The original r3 reference, all r5/r6
evidence, formal repository RTL, models and SDK are preserved.

The new protected ledger contains 937 paths: exactly one functional reader change,
25 reversible ASCII root-path changes in cached controls, and 911 identical files.
XPR is outside that ledger; its only offline edit is the single `Project.Path`
attribute, verified by exact inverse bytes. No XCI/BD serialization, target
regeneration, IP upgrade, global library write, clock/constraint/waiver change or
r6 extra postroute optimization is performed.

The 25 path-control changes are 24 original OOC native Tcl scripts and the old
derived `procise_run_disable_icap.tcl`. Cached OOC scripts are not launch targets.
Older factory paths in cached comments/metadata are preserved; they cannot be used
as actual sources by the new top native script. The new top native audit rejects
old workspace references and allows absolute paths only in REF7 or the fixed
Vivado installation. All 11 original PS DCPs and managed `ps_ai.bd` must remain in
the actual dependency graph. Full PS retains module name `ps_ai`, the 12 original
other modules, original timescale and the three previously reviewed passive taps.

`continue_hdmi_reader_idle_candidate.py` defaults to read-only `inspect`. Root owns
explicit EDA invocations, one stage at a time:

1. `setup`: actual project/compile-order/OOC/locked-IP/syntax audit; no IP generation.
   Create `synth_read_v3r7_preview_r2` and request scripts only, never execution. Freeze
   and audit its complete native Tcl before allowing the separate actual run.
2. `synthesis`: fresh `synth_read_v3r7`, original synthesis hook; actual new native
   script must add the new REF's original managed BD once. Its complete bytes must
   equal the reviewed preview after exactly the recorded run-name substitutions,
   with exact inverse reconstruction; any other change stops the stage.
3. `constraints`: rerun original CDC, 2768-bit stable-bus endpoints and clock audit;
   an independently reviewed new r7 constraint receipt is required next.
4. `place`: fresh `impl_read_v3r7` parented to the new synthesis; original
   `Performance_NetDelay_high`, `ExtraNetDelay_high`, `AggressiveExplore`, original
   HDMI/observer OPT_PRE and all original hooks. Stop at completed physical
   optimization and save a new physical checkpoint.
5. `route`: resume that actual completed new project run only, original
   `NoTimingRelaxation` and complete original JFM route_post. Save a new routed DCP.
6. `reports`: original complete timing/DRC/CDC/exception/clock reports plus read
   observer endpoint coverage, followed by the independent new formal gate.

Current stage names are `read-v3r7-setup-r2` and
`read-v3r7-{synthesis,constraints,place,route,reports}`. The original failed
`read-v3r7-setup` is retained without a `phase-review.json`.
`input-proof.json` records preparation/source/install/managed/source-driver hashes;
`phase-review.json` is written exclusively only after actual tool exit zero and
post-stage identities/checkpoints/native audits pass. Preparation/phase pass does
not mean the formal timing/DRC gate passed or the DMA/board fault was repaired.

The installed 2018.3 has actual evidence that a run launched with `-scripts_only`
cannot subsequently be launched normally without reset (`read-v3r2-synthesis`,
13.016s exit 1). The separate preview avoids resetting that run or touching OOC
runs. Existing r2/r3 synth native scripts normalize to identical bytes after only
their run-name substitution. This is supporting evidence; r7 still requires its
own actual preview, strict new-REF path audit and actual full-byte comparison.

Local preparation actually completed in 165.547s (4,726 files, 2,630,972,361 bytes).
The actual initial preparer is preserved under E7/preparation; the later explicit
`.jobs`/reparse/destination safeguards are a separate source revision and were
not falsely attributed to that execution. A 23.782s supplemental review verified
every old/new copied file, independent destination file IDs/nlink1, both trees'
resolved/reparse boundaries and exactly 27 whole-clone changed files (25 path
controls, one reader, one XPR). The actual copy already excluded `.runs/.jobs`
through its 24-OOC-only directory whitelist. E7/driver-preparation-r2 has 46 pure
checks with zero process attempts; r1 retains a failed mocked-stat fixture.

The first setup driver frozen for root review was SHA256
`90ec34ab996a63edefaf8a7af762ac16460f1a282115000d825c4f2768a1c8e6`.
Root actually executed its setup: Vivado exited zero after 80.093s, while the
Python wrapper exited one because its full-mtime equality guard rejected cache
metadata refresh. That setup is a failure and produced no phase-pass receipt.
All 451 cache file names, SHA256 and sizes remained identical. Exactly 24
original OOC `gen_run.xml` files had new mtimes; the other 427 files retained
their mtimes. Both sets of full XML bytes, inventories and timestamp observations
are retained in E7/setup-cache-failure-r1. Source/PS/DCP/native/log bytes, original
REF/XPR and all 41 installed files were unchanged. The exact internal serializer
call touching the timestamps is unknown; no extra EDA trace was run.

Root approved the narrow local guard revision. The current driver is SHA256
`aa175d681abc632625df8e7ec7a74cf332fa59a1dd3e0ab39066074c1696f2a6`.
It permits mtime changes only for the exact 24 original OOC `gen_run.xml` paths
when their bytes/SHA/size are identical. All 451 names/content and all other 427
mtimes remain strict. Before/after inventories, comparison and all 24 raw metadata
files are saved before rejecting a failed comparison. Timestamps are never
restored to conceal changes. The old failed setup is not promoted to pass.

New setup-r2 begins only from the exact failed-setup XPR snapshot and its preserved
Scripts Generated preview state. The old preview remains unexecuted. Formal
synthesis must inherit the exact new setup-r2 XPR and its newly reviewed preview.
E7/driver-cache-policy-r3 records 46 basic checks plus 1367 finite mutations,
including every cache file's content/size, every forbidden mtime and every allowed
metadata mtime, with zero EDA/process attempts inside the mocks. These source and
mock results do not claim that setup-r2 or synthesis has been executed.

The unchanged `eda_owned_stage.py` owns process/CPU/log monitoring: initial 180s,
ceiling 1800s for synthesis/place/route and 540s for setup/constraints/reports.
Root may review a new bounded budget after preserving a timeout; failed or live
loads are not automatically retried. No bit, ICAP, BOOT, SSH, serial, reboot or
board entry point exists here. Onsite observation work remains paused and there
is no new BOOT/reboot authorization.
