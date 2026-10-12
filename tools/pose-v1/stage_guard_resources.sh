#!/bin/sh
set -eu
dir=${1:?fresh evidence directory}
test ! -e "$dir"
mkdir "$dir"
for name in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$name" > "$dir/$name"; done
dmesg > "$dir/dmesg"
ps -eo pid,comm,args > "$dir/processes"
ss -ltnp > "$dir/ports"
date -u > "$dir/time"
