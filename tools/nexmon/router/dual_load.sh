#!/bin/sh
set -e
cd "$(dirname "$0")"
test ! -e armed
test ! -e restored
test "$(openssl dgst -sha256 dhd-test.ko | awk '{print $NF}')" = "$(cat candidate.sha256)"
test "$(openssl dgst -sha256 /lib/modules/4.1.27/extra/dhd.ko | awk '{print $NF}')" = "$(cat stock.sha256)"
chmod 700 nexutil makecsiparams capture-metadata restore.sh watchdog.sh
cut -d. -f1 /proc/uptime > lease
cp lease started
touch armed
sh -c 'trap "" HUP; exec sh ./watchdog.sh' </dev/null >watchdog.log 2>&1 &
echo "$!" > watchdog.pid
completed=0
removed=0
trap 'if [ "$completed" -ne 1 ]; then if [ "$removed" -eq 1 ]; then sh restore.sh; else rm -f armed; fi; fi' 0
rmmod dhd
removed=1
insmod ./dhd-test.ko
ifconfig eth6 up
wl -i eth6 radio on
wl -i eth6 mpc 0
wl -i eth6 up
wl -i eth6 ver
wl -i eth6 revinfo
cut -d. -f1 /proc/uptime > lease
completed=1
echo TEST_MODULE_LOADED=1
