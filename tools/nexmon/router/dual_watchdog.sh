#!/bin/sh
cd "$(dirname "$0")" || exit 1
while [ -e armed ]; do
 sleep 3
 [ -e armed ] || exit 0
 now=$(cut -d. -f1 /proc/uptime)
 last=$(cat lease)
 start=$(cat started)
 if [ "$((now-last))" -gt 240 ] || [ "$((now-start))" -gt 1200 ]; then
  echo 'Lease expired: stop test and restore own stock driver'
  sh restore.sh > watchdog-restore.log 2>&1
  exit $?
 fi
done
