"""Bounded host pacer: READY/GO anchors the epoch before any emitted tick."""
import sys
import time

count = int(sys.argv[1])
hz = float(sys.argv[2])
print('READY', flush=True)
if sys.stdin.readline().strip() != 'GO':
    raise RuntimeError('Missing host start handshake')
epoch = time.perf_counter_ns() + 200_000_000
minimum = epoch
for index in range(count):
    deadline = max(epoch + round(index * 1e9 / hz), minimum)
    while True:
        remaining = deadline - time.perf_counter_ns()
        if remaining <= 0:
            break
        if remaining > 1_500_000:
            time.sleep((remaining - 1_000_000) / 1e9)
    print(index, flush=True)
    # At most one unconsumed tick; host backpressure cannot build an unbounded
    # readline/pipe queue. Deadlines continue to use the original epoch.
    acknowledgement = sys.stdin.readline().split()
    if len(acknowledgement) != 2 or acknowledgement[0] != 'NEXT':
        raise RuntimeError('Missing host tick acknowledgement')
    delay_ns = int(acknowledgement[1])
    if delay_ns < 0:
        raise RuntimeError('Negative host pacing delay')
    minimum = time.perf_counter_ns() + delay_ns
