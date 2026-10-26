#!/bin/sh
# First install only; run on the matching router after uploading its package.
# Usage: sh install.sh rx1|tx|rx2|rx3 /tmp/ROLE-autostart.tar.gz SHA256
set -e
case "$1" in
 rx1) ip=192.168.50.1; mac=04:d4:c4:b5:83:40;;
 tx) ip=192.168.50.2; mac=f0:2f:74:39:45:68;;
 rx2) ip=192.168.50.3; mac=04:d9:f5:92:29:20;;
 rx3) ip=192.168.50.4; mac=04:d4:c4:1a:cb:68;;
 *) exit 2;;
esac
P=/jffs/pose180-csi
[ ! -e "$P" ]
[ "$(nvram get productid)" = RT-AC86U ]
[ "$(nvram get lan_ipaddr)" = "$ip" ]
[ "$(nvram get lan_hwaddr | tr A-F a-f)" = "$mac" ]
[ "$(nvram get jffs2_scripts)" = 1 ]
[ "$(openssl dgst -sha256 "$2" | awk '{print $NF}')" = "$3" ]
mkdir "$P"
tar xzf "$2" -C "$P"
cp -p /jffs/scripts/services-start "$P/services-start.before"
cp -p /jffs/scripts/services-stop "$P/services-stop.before"
# These four inspected hooks invoke KoolShare then return (no early exit).
printf '\n# pose180-csi autostart\nsh /jffs/pose180-csi/service.sh boot </dev/null >/dev/null 2>&1 &\n' >> /jffs/scripts/services-start
printf '\n# pose180-csi orderly stop\nsh /jffs/pose180-csi/service.sh stop </dev/null >/dev/null 2>&1\n' >> /jffs/scripts/services-stop
chmod 700 "$P/service.sh" /jffs/scripts/services-start /jffs/scripts/services-stop
sync
echo "installed $1; run service.sh start or reboot for verification"
