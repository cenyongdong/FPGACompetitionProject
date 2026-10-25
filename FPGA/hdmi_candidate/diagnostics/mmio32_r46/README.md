# r46 offline MMIO32 correction

No board access, BOOT change or SDK load was performed here. r45 remains closed
and unchanged. This directory supplies software inputs for a separately
authorized future test; it does not activate a new package.

`gates/capture_deferred.py` retains the existing snapshot/consume/checker-rearm
interface and all admission/conservation/one-shot/no-retry boundaries. Its
`NativeMMIO32` class loads sibling `libmmio32.so` through ctypes before opening
`/dev/mem`. Deploy the script and `package/libmmio32.so` together in the flat
package; the parent binds the library through both controller/file identities.
There is no separate Python native adapter module.

The native C source is `native/mmio32.c`. A successful operation validates
natural 4-byte alignment and performs one volatile uint32_t load or store.
AArch64 uses `dmb sy` before and `dsb sy` after the access. The read output is
separate ctypes-owned CPU memory. No memset, buffer packing, reset, mapping,
command construction or retry exists in the C helper. The Python caller retains
the 4 KiB mapping/range, command whitelist, boot check and persisted attempt
before the single native write. Barriers do not replace acknowledgement checks.

Actual release disassembly (`build/aarch64-objdump.txt`) shows the incoming device
pointer copied from x0 to x2. `mmio32_write32` contains one `str w1, [x2]` at
0x5a0; `mmio32_read32` contains one `ldr w2, [x2]` at 0x570. The read function's
`str w2, [x1]` is its ordinary CPU output. No physical AXI beat count is claimed.
The ELF is little-endian AArch64, with no DT_NEEDED SDK dependency.

CPython's pack_into zero-first behavior was reproduced using ordinary CPU
bytearrays, including the parent agent's board Python 3.8.10 CPU-only test:
a5a5a5a5 → 00000000 inside Value.__index__ → 01000000 finally. The installed
Python host test reproduces the same API behavior. This is evidence of a buffer
pre-clear, not a captured r45 CPU instruction or measured AXI write count. The
new device path uses no struct.pack_into/unpack_from. Its sole pack_into use is
the explicitly CPU-only counterexample test.

Command failures now save `failure_kind`, the last complete raw header, total
elapsed time, ACK elapsed time and configured ACK deadline. Hardware status bit1
(status2) is `command_error`, even when a deadline also expired; an elapsed wait
is separately `ack_deadline_elapsed`. Native write/header failures and generation
changes remain distinct, and no failed command is repeated. `command_failed`
evidence and `result.json.command_failure` retain these details.

Existing FPAI GCC 9.4 and objdump 2.34 built and inspected the release library.
Existing Windows GCC 16.2 built the same C source as a host DLL for real ctypes
calls into ordinary CPU memory. `build/build-record.json` retains exact commands,
native outputs, exit codes and durations. `build/native-identities.json` contains
source/script/library identities; the host DLL is only a test artifact.

Offline results: `gates/capture-tests.json` **11/11**, including single command,
no retry, preserved last status2 header and elapsed-time assertions; and
`build/mmio32-tests.json` **5/5**, including actual ctypes load/store, alignment
rejection, one native command call, CPU zero-first counterexample and release
instruction checks. These establish no board pass. The FPAI container was
initially exited, started only for this build, checked to have no remaining build
process, stopped and confirmed exited afterwards.
