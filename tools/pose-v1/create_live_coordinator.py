"""Readiness handshake in an external runner; binary/package/protocol unchanged."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'tools/pose-v1/run-live-coordinated.sh';assert not target.exists()
s=(root/'tools/pose-v1/run-live-stage.sh').read_text()
old='''timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log"
code=$?'''
new='''if test "$stage" = host-check; then
    timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log"
    code=$?
else
    timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log" &
    job=$!
    tries=0
    while test "$tries" -lt 80; do
        if grep -q '"event":"ready"' "$run/results/network/events.jsonl" 2>/dev/null; then
            printf 'LIVE_READY %s\\n' "$stage"
            break
        fi
        if ! kill -0 "$job" 2>/dev/null; then break; fi
        tries=$((tries+1))
        sleep 0.1
    done
    wait "$job"
    code=$?
fi'''
assert s.count(old)==1;s=s.replace(old,new);target.write_bytes(s.encode());print(target)
