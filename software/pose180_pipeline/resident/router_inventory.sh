#!/bin/sh
set -e
printf 'LAN_MAC='; cat /sys/class/net/br0/address
printf 'RADIO_MAC='; cat /sys/class/net/eth6/address
printf 'SSH_MODE='; nvram get sshd_enable
printf 'SSH_PORT='; nvram get sshd_port
printf 'UPTIME='; cat /proc/uptime
printf 'RADIO_UP='; /usr/sbin/wl -i eth6 isup
printf 'RADIO_AP='; /usr/sbin/wl -i eth6 ap
printf 'RADIO_MONITOR='; /usr/sbin/wl -i eth6 monitor
printf 'CURRENT_MODULE='; cat /proc/modules | head -4
ls -l /tmp/nexmon-multirx-20261025-r1-*/dhd*.ko /tmp/nexmon-multirx-20261025-r1-*/nexutil /tmp/nexmon-multirx-20261025-r1-*/makecsiparams
