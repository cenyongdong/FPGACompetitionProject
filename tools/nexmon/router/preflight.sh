#!/bin/sh
# Read-only probe. No nvram set/commit, driver load, radio changes or reboot.
set -u
probe() {
    printf '\nBEGIN %s\n' "$1"
    shift
    "$@" 2>&1
    result=$?
    printf 'EXIT %s\n' "$result"
}
printf 'NEXMON_PREFLIGHT_VERSION=2\n'
probe kernel uname -a
for key in productid odmpid hardware_version bl_version firmver buildno extendno wl0_ifname wl1_ifname; do
    probe "nvram:$key" nvram get "$key"
done
probe filesystems df -k /tmp /jffs
probe modules cat /proc/modules
for name in wl openssl md5sum sha256sum strings modinfo tcpdump timeout; do
    # ASUS BusyBox sh may not provide the POSIX command builtin.
    probe "tool:$name" which "$name"
done
for key in wl0_ifname wl1_ifname; do
    iface=$(nvram get "$key" 2>/dev/null)
    case "$iface" in
        ''|*[!a-zA-Z0-9_.:-]*) printf 'SKIP invalid interface for %s\n' "$key"; continue ;;
    esac
    probe "$iface:revision" /usr/sbin/wl -i "$iface" revinfo
    probe "$iface:version" /usr/sbin/wl -i "$iface" ver
    probe "$iface:channel" /usr/sbin/wl -i "$iface" chanspec
done
printf '\nNEXMON_PREFLIGHT_COMPLETE=1\n'
# Individual EXIT values require review. Completion is not compatibility approval.
