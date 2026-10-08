"""Derive the isolated preflight/timeout/evidence runner; keep resident runner frozen."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'tools/pose-v1/run-live-stage.sh';assert not target.exists()
s=(root/'tools/pose-v1/run-resident-stage.sh').read_text()
s=s.replace('resident-three','live-three').replace('resident-27','live-27').replace('pose_resident_check','pose_live_pipeline_check')
s=s.replace("pipeline_build_reviewed","live_build_reviewed").replace("pipeline_stage_passed","live_stage_passed")
s=s.replace('--allow-vpu-stream;','--allow-vpu-stream --allow-network;')
anchor='set +e\ntimeout --signal=TERM --kill-after=5s';assert s.count(anchor)==1
au='''set +e
au_code=0
if test "$stage" = host-check; then
    cp "$work/pose_access_unit_selftest" "$run/pose_access_unit_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_access_unit_selftest" > "$run/AU.stdout.log" 2> "$run/AU.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/AU.exit.txt"
fi
if test "$au_code" = 0; then
timeout --signal=TERM --kill-after=5s'''
s=s.replace(anchor,au)
s=s.replace('code=$?\nset -e','code=$?\nelse\ncode=$au_code\nfi\nset -e')
target.write_bytes(s.encode());print(target)
