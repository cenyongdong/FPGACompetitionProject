#!/bin/sh
# Files live only in the explicitly staged RAM directory; no autostart install.
set -eu
cd "$(dirname "$0")"
. ./guard.conf
case "${1:-}" in
 start)
  test -e armed && test ! -e restored
  exec ./router_guard "$GUARD_ROLE" "$PWD" "$GUARD_SECONDS" 192.168.50.49 39033 eth6
  ;;
 status) cat guard-status.json ;;
 stop) touch stop.request; echo 'Source stop requested; guard owns restoration.' ;;
 pause)
  case "${2:-}" in ''|*[!0-9]*) exit 2;; esac
  test "$2" -gt 0 && test "$2" -le 120 && test "$GUARD_ROLE" = rx
  printf '%s\n' "$2" > pause.seconds
  ;;
 *) echo 'usage: router_ctl.sh start|status|stop|pause SECONDS' >&2; exit 2 ;;
esac
