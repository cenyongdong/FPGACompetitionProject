#!/bin/sh
# Persistent mode has no run-duration cap. Only the local heartbeat is watched.
cd "$(dirname "$0")" || exit 1
while [ -e armed ]; do
 sleep 3
 [ -e armed ] || exit 0
 now=$(cut -d. -f1 /proc/uptime)
 last=$(cat lease 2>/dev/null)
 case "$last" in ''|*[!0-9]*) last=0;; esac
 limit=300
 [ ! -e guard-status.json ] || limit=20
 [ "$((now-last))" -gt "$limit" ] || continue
 printf 'heartbeat_expired now=%s last=%s limit=%s\n' "$now" "$last" "$limit" > watchdog-trigger.log
 touch stop.request
 # Let the guard finish its own stop/proof/free/restore sequence. A slow or
 # unresponsive owner must not race an independent driver unload.
 i=0
 while [ "$i" -lt 75 ]; do
  i=$((i+1))
  [ ! -e armed ] && exit 0
  [ ! -e guard-final.json ] || exit 1
  sleep 1
 done
 echo 'manual_recovery_required; no concurrent unload' >> watchdog-trigger.log
 exit 1
done
