#!/bin/sh
# Installed entry point. Persistent assets are read-only during normal running.
P=/jffs/pose180-csi
R=/tmp/pose180-csi
LOCK=/tmp/pose180-csi.lock
owned_guard() {
 pid=$(cat "$R/guard.pid" 2>/dev/null)
 case "$pid" in ''|*[!0-9]*) return 1;; esac
 [ "$(readlink /proc/$pid/cwd)" = "$R" ] &&
 [ "$(readlink /proc/$pid/exe)" = "$R/router_guard" ] && kill -0 "$pid" 2>/dev/null
}
case "${1:-status}" in
 boot)
  [ -f "$P/enabled" ] || exit 0
  # services-start may be re-entered. Never reload a radio twice automatically.
  mkdir /tmp/pose180-csi.boot-attempt 2>/dev/null || exit 0
  exec sh "$P/service.sh" start
 ;;
 enable) touch "$P/enabled"; exec sh "$P/service.sh" start;;
 disable) rm -f "$P/enabled"; exec sh "$P/service.sh" stop;;
 start)
  [ -f "$P/enabled" ] || { echo disabled; exit 1; }
  owned_guard && { echo already_running; exit 0; }
  mkdir "$LOCK" 2>/dev/null || { echo starting_or_latched; exit 0; }
  if [ -d "$R" ]; then
   if [ ! -e "$R/restored" ]; then
    echo 'Previous runtime is not restored; inspect before retrying.'
    rmdir "$LOCK"; exit 1
   fi
   # Fixed owned paths, one previous generation; never erase other /tmp work.
   rm -rf /tmp/pose180-csi.previous
   mv "$R" /tmp/pose180-csi.previous || exit 1
  fi
  mkdir "$R" || exit 1
  cp "$P"/runtime/* "$R"/ || exit 1
  touch "$R/continuous"
  printf 'waiting_radio\n' > "$R/service.state"
  sh -c 'trap "" HUP; exec sh /jffs/pose180-csi/service.sh run' </dev/null >/dev/null 2>&1 &
  echo "$!" > "$R/service.pid"
  echo starting
 ;;
 run)
  cd "$R" || exit 1
  . ./identity.conf
  # LAN is independent of the replaced WLAN module. Wait for boot services,
  # interface creation and the expected router identity, not PC/board order.
  ready=0
  i=0
  while [ "$i" -lt 180 ]; do
   i=$((i+1))
   if [ -e stop.request ]; then
    echo stopped_before_load > service.state; touch restored; rmdir "$LOCK"; exit 0
   fi
   if [ "$(cut -d. -f1 /proc/uptime)" -ge 60 ] &&
      [ "$(nvram get lan_ipaddr)" = "$ROUTER_IP" ] &&
      [ "$(nvram get lan_hwaddr | tr A-F a-f)" = "$ROUTER_MAC" ] &&
      [ -d /sys/class/net/eth6 ] && wl -i eth6 ver >/dev/null 2>&1; then ready=1; break; fi
   sleep 1
  done
  if [ "$ready" -ne 1 ]; then echo radio_not_ready > service.state; exit 1; fi
  # An independently deployed finite trial owns the radio if it is running.
  if pidof router_guard capture-metadata-stream >/dev/null 2>&1; then
   echo other_source_active > service.state; exit 1
  fi
  echo loading_radio > service.state
  if ! sh load.sh > load.log 2>&1; then echo load_failed > service.state; exit 1; fi
  if [ -e stop.request ]; then sh restore.sh > stop-before-guard.log 2>&1; rmdir "$LOCK"; exit 0; fi
  if ! ./router_guard "$GUARD_ROLE" "$R" 0 192.168.50.49 39033 eth6 > launch.json 2>&1; then
   echo guard_launch_failed > service.state
   sh restore.sh > launch-restore.log 2>&1
   exit 1
  fi
  echo running > service.state
 ;;
 stop)
  [ -d "$R" ] || exit 0
  touch "$R/stop.request"
  i=0
  while [ "$i" -lt 90 ]; do
   i=$((i+1))
   if [ -e "$R/restored" ] && ! owned_guard; then
    rmdir "$LOCK" 2>/dev/null || true
    echo stopped; exit 0
   fi
   sleep 1
  done
  echo 'Stop pending or restore failed; no forced driver unload.'; exit 1
 ;;
 status)
  [ ! -e "$P/enabled" ] || echo enabled
  for f in service.state guard-status.json guard-final.json watchdog-trigger.log; do
   [ ! -f "$R/$f" ] || cat "$R/$f"
  done
 ;;
 *) echo 'usage: service.sh enable|disable|start|stop|status|boot'; exit 2;;
esac
