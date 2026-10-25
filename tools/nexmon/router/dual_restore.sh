#!/bin/sh
set -e
cd "$(dirname "$0")"
[ ! -e restored ] || exit 0
mkdir restore-lock || exit 75
trap 'rmdir restore-lock' 0
test "$(openssl dgst -sha256 /lib/modules/4.1.27/extra/dhd.ko | awk '{print $NF}')" = "$(cat stock.sha256)"
if [ -e tx-role ]; then
 ./nexutil -Ieth6 -s431 || true
 ./nexutil -Ieth6 -s432 || true
fi
if [ -e disabled.params ]; then
 ./nexutil -Ieth6 -s500 -b -l34 -v "$(cat disabled.params)" || true
fi
if [ -e capture.pid ]; then
 p=$(cat capture.pid)
 if [ -r /proc/$p/cmdline ] && grep -q 'nexmon-dual-20261022-r2/capture-metadata' /proc/$p/cmdline; then
  kill -TERM "$p"
  sleep 1
 fi
fi
wl -i eth6 monitor 0 || true
wl -i eth5 monitor 0 || true
if grep -q '^dhd ' /proc/modules; then rmmod dhd; fi
insmod /lib/modules/4.1.27/extra/dhd.ko
service restart_wireless
sleep 4
for i in eth5 eth6; do
 echo RESTORED_INTERFACE=$i
 wl -i "$i" ver
 wl -i "$i" isup
 wl -i "$i" monitor
 wl -i "$i" chanspec
done
touch restored
rm -f armed
echo STOCK_RUNTIME_RESTORED=1
