#!/usr/bin/env bash
set -euo pipefail
test ! -e /work/nexmon
mkdir -p /work/nexmon
cp -a /input/nexmon/.git /work/nexmon/.git
cd /work/nexmon
git config core.symlinks true
git config core.filemode true
git config core.sparseCheckout true
git config http.lowSpeedLimit 1000
git config http.lowSpeedTime 90
cp /kit/environment/sparse-paths.txt .git/info/sparse-checkout
git -c core.symlinks=true read-tree -mu HEAD
git rev-parse HEAD
echo 'LINUX_SOURCE_CHECKOUT_COMPLETE=1'
