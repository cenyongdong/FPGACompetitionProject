#!/bin/sh
# Run only after the owned board listener and existing NMD3 radio are ready.
# This forwards the original PCAP stream directly; it does not configure radio.
set -u
if [ "$#" -ne 4 ]; then
 echo 'usage: router_send.sh CAPTURE_STREAM NEW_RAM_DIRECTORY BOARD_IPV4 PORT' >&2
 exit 2
fi
capture=$1
folder=$2
board=$3
port=$4
case "$capture" in /tmp/*/capture-metadata-stream) ;; *) echo 'Require the explicit staged capture tool' >&2; exit 2;; esac
case "$folder" in /tmp/nexmon-direct-*) ;; *) echo 'Require a new task RAM directory' >&2; exit 2;; esac
case "$folder" in *..*|*[!a-zA-Z0-9_./-]*) exit 2;; esac
[ "$board" = 192.168.50.49 ] || { echo 'Unexpected owned board endpoint' >&2; exit 2; }
[ "$port" = 39033 ] || { echo 'Unexpected capture port' >&2; exit 2; }
[ -x "$capture" ] && [ ! -e "$folder" ] || exit 2
mkdir -m 700 "$folder" || exit 2
fifo=$folder/stream.fifo
mkfifo "$fifo" || exit 2
pid=
cleanup() {
 if [ -n "$pid" ] && [ -r "/proc/$pid/cmdline" ] && grep -q "$capture" "/proc/$pid/cmdline"; then
  kill -TERM "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
 fi
 rm -f "$fifo"
}
trap cleanup 0
trap 'exit 130' INT TERM HUP
"$capture" eth6 - 16 24000 > "$fifo" 2> "$folder/capture.native.json" &
pid=$!
nc -w 25 "$board" "$port" < "$fifo" > "$folder/network.stdout" 2> "$folder/network.stderr"
network=$?
wait "$pid"
native=$?
pid=
printf '{"capture_exit":%s,"network_exit":%s,"pc_relay":false}\n' "$native" "$network" > "$folder/exit.json"
[ "$native" -eq 0 ] || exit "$native"
[ "$network" -eq 0 ] || exit "$network"
