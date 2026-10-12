"""Local QPC pacing only; no system timer changes or board access."""
import time
TAIL_NS=2_000_000
MAX_LATE_NS=20_000_000
def wait_until(deadline_ns):
    while True:
        now=time.perf_counter_ns()
        if now>=deadline_ns:
            if now-deadline_ns>MAX_LATE_NS:raise TimeoutError('Precise sender lateness exceeds20ms; no burst catchup')
            return now
        remaining=deadline_ns-now
        if remaining>TAIL_NS:time.sleep((remaining-TAIL_NS)/1e9)
        # At most the final2ms is polled; QPC is monotonic and checked each turn.
