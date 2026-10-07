#!/bin/sh
# Approved read-only metadata audit. No Session, Device::Open, model or install.
# Run in the existing Lite SSH terminal; keep complete stdout/stderr.
cd /tmp/pose-v1-inference-20261005 || exit 1

audit_step() {
    printf '\n=== %s ===\n' "$1"
    shift
    "$@"
    audit_rc=$?
    printf 'audit_command_exit=%s\n' "$audit_rc"
    return "$audit_rc"
}

audit_step package_versions dpkg-query -W -f='${Package} ${Architecture} ${Version} ${Status}\n' icraft:arm64 customop:arm64 || exit 1
audit_step installed_icraft_integrity dpkg -V icraft:arm64
printf '\n=== relevant_package_files ===\n'
dpkg-query -L icraft:arm64 | grep -E 'hostbackend|cuda|matmul'
printf 'file_filter_exit=%s\n' "$?"
audit_step host_library_path readlink -f /lib/aarch64-linux-gnu/libicraft_hostbackend.so
audit_step host_library_sha256 sha256sum /lib/aarch64-linux-gnu/libicraft_hostbackend.so
audit_step host_export_targets cat /usr/cmake/icraft-hostbackend-targets-aarch64.cmake
audit_step host_export_release cat /usr/cmake/icraft-hostbackend-targets-aarch64-release.cmake
printf '\n=== readelf_availability ===\n'
command -v readelf
printf 'readelf_query_exit=%s\n' "$?"
printf '\n=== audit_finished_review_required ===\n'
