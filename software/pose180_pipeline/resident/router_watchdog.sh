#!/bin/sh
# Guard heartbeat, not PC connectivity, renews the local lease.
cd "$(dirname "$0")" || exit 1
while [ -e armed ]; do
 sleep 3
 [ -e armed ] || exit 0
 now=$(cut -d. -f1 /proc/uptime)
 last=$(cat lease 2>/dev/null)
 case "$last" in ''|*[!0-9]*)
  sleep 1
  last=$(cat lease 2>/dev/null)
  case "$last" in ''|*[!0-9]*) last=0;; esac
 ;; esac
 start=$(cat started)
 limit=300
 [ ! -e guard-status.json ] || limit=20
 if [ "$((now-last))" -gt "$limit" ] || [ "$((now-start))" -gt 2400 ]; then
  printf 'watchdog now=%s last=%s start=%s limit=%s\n' "$now" "$last" "$start" "$limit" > watchdog-trigger.log
  touch stop.request
  sleep 2
  sh restore.sh > watchdog-restore.log 2>&1
  exit $?
 fi
done
