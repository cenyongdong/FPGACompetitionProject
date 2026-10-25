"""Run generated firmware C with native mock wrappers, without a device/toolchain install."""
import argparse
from pathlib import Path
import subprocess
import sys

from prepare_tx_task import prepare


STUBS = r'''
#ifndef PIW_NATIVE_STUBS_H
#define PIW_NATIVE_STUBS_H
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <limits.h>
typedef uint32_t uint32;
typedef uint8_t uint8;
typedef unsigned int uint;
struct d11regs { uint8 reserved[0x180]; volatile uint32 tsf_timerlow; };
struct wlc_hw { int up, corerev; };
struct wlc_info {
    uint8 reserved[0x10]; struct d11regs *regs;
    struct wlc_hw *hw; void *osh, *wl;
};
static unsigned timer_adds, timer_dels, timer_frees, packets, allocations;
static unsigned fail_alloc, advance_on_send, discarded;
static void (*during_alloc)(void);
static struct d11regs mock_regs;
static struct wlc_hw mock_hw = {1, 0x41};
static struct wlc_info mock_wlc = {{0}, &mock_regs, &mock_hw, 0, 0};
static int firmware_printf(const char *format, ...) { (void)format; return 0; }
#define printf firmware_printf
static void *mallocz(unsigned n) { return calloc(1, n); }
static void *pkt_buf_get_skb(void *osh, unsigned n) {
    (void)osh; ++allocations;
    if (during_alloc) during_alloc();
    return fail_alloc ? 0 : malloc(n);
}
static void pkt_buf_free_skb(void *osh, void *p, int send) { (void)osh; (void)send; ++discarded; free(p); }
static void *skb_pull(void *p, unsigned n) { return (uint8 *)p + n; }
static void sendframe(struct wlc_info *wlc, void *p, unsigned fifo, unsigned rate) {
    (void)fifo; (void)rate; ++packets; free(p);
    wlc->regs->tsf_timerlow += advance_on_send;
}
static void wl_add_timer(void *wl, void *timer, unsigned ms, int periodic) {
    (void)wl; assert(timer); assert(ms); assert(!periodic); ++timer_adds;
}
static void wl_del_timer(void *wl, void *timer) { (void)wl; assert(timer); ++timer_dels; }
static void wl_free_timer(void *wl, void *timer) { (void)wl; ++timer_frees; free(timer); }
static void *wl_init_timer(void *wl, void (*f)(void *), void *ctx, const char *name) {
    (void)wl; (void)f; (void)ctx; (void)name; return malloc(1);
}
static void set_mpc(struct wlc_info *wlc, int value) { (void)wlc; (void)value; }
static void set_scansuppress(struct wlc_info *wlc, int value) { (void)wlc; (void)value; }
static void set_intioctl(struct wlc_info *wlc, int cmd, int value) { (void)wlc; (void)cmd; (void)value; }
static int wlc_stf_doiovar(struct wlc_info *wlc, int a, int b, int c, void *d, unsigned e,
                         int f, int g, int h, int i) {
    (void)wlc; (void)a; (void)b; (void)c; (void)d; (void)e; (void)f; (void)g; (void)h; (void)i;
    return 0;
}
static int wlc_ioctl(struct wlc_info *wlc, int cmd, char *arg, int len, void *iface) {
    (void)wlc; (void)cmd; (void)arg; (void)len; (void)iface; return -1;
}
#define IOCTL_SUCCESS 0
#define IOCTL_ERROR -1
#define WLC_SET_LRL 1
#define WLC_SET_SRL 2
#define GenericPatch4(a,b) static int native_patch_unused
#define CHIP_VER_BCM4366c0 0
#define FW_VER_10_10_122_20 0
#endif
'''

HARNESS = r'''
#include "native_stubs.h"
#include "../derivative/src/tx_task.c"
#include "../derivative/src/ioctl.c"
#undef printf

static int call(int cmd, void *arg, unsigned len) {
    return wlc_ioctl_hook(&mock_wlc, cmd, (char *)arg, len, 0);
}
static void status(uint32 out[8]) { assert(call(435, out, 32) == 0); }
static void configure(unsigned mode, unsigned rate, unsigned slots) {
    uint8 input[38] = {0}; uint32 values[3] = {rate, slots, 0};
    input[1] = mode; memcpy(input+2, values, 12); input[14] = 0x08;
    memset(input+18, 0xff, 6);
    assert(call(429, input, sizeof(input)) == 0);
    assert(tx_ctx && tx_ctx->task_token);
}
static int renew(unsigned token, unsigned seq) {
    uint32 input[3] = {PIW_TX_LEASE_MAGIC, token, seq};
    return call(434, input, sizeof(input));
}
static void clear_context(void) {
    if (tx_ctx) {
        assert(call(431, 0, 0) == 0);
        assert(call(432, 0, 0) == 0);
    }
    mock_hw.up = 1; fail_alloc = advance_on_send = 0; during_alloc = 0;
}
static void stop_during_alloc(void) { assert(call(431, 0, 0) == 0); }
static void expire_during_alloc(void) { mock_regs.tsf_timerlow = tx_ctx->lease_deadline_tsf; }
static void due(void) { mock_regs.tsf_timerlow = tx_ctx->next_due; tx_task_tx_now(tx_ctx); }
static void test_leases(void) {
    uint32 s[8], first, token, old_due, old_fraction, old_timer, i;
    mock_regs.tsf_timerlow = 100;
    configure(3, 300, 18000); status(s); token = s[2];
    assert(s[0] == PIW_TX_LEASE_MAGIC && s[1] == 1 && s[3] == 0 && s[4] == 0 && !s[5] && !s[6]);
    assert(renew(token, 1) == IOCTL_ERROR); /* configured is not running */
    assert(call(430, 0, 0) == 0); status(s);
    assert(s[4] == 60000 && s[5] == 1);
    first = tx_ctx->next_due;
    for (i = 0; i < 72000; ++i) { /* 240 seconds, same task/token/timer */
        if (i && i % 3000 == 0) {
            old_due = tx_ctx->next_due; old_fraction = tx_ctx->fraction; old_timer = timer_adds;
            assert(renew(token, i / 3000) == 0);
            assert(tx_ctx->next_due == old_due && tx_ctx->fraction == old_fraction && timer_adds == old_timer);
            assert(renew(token, i / 3000) == IOCTL_ERROR);
        }
        assert(tx_ctx->next_due == first + (uint32)(((uint64_t)i * 10000) / 3));
        due(); assert(tx_ctx->running && !tx_ctx->error);
    }
    status(s); assert(s[2] == token && s[3] == 23 && s[7] == 23);
    assert(tx_ctx->submitted == 72000 && tx_ctx->skipped == 0);
    assert(tx_ctx->first_enqueue_tsf == first);
    old_due = tx_ctx->lease_deadline_tsf;
    assert(renew(token+1, 24) == IOCTL_ERROR && renew(token, 0) == IOCTL_ERROR);
    assert(tx_ctx->lease_deadline_tsf == old_due && !tx_ctx->error);
    { uint32 in[3] = {0, token, 24}; assert(call(434, in, 12) == IOCTL_ERROR); }
    { uint32 in[3] = {PIW_TX_LEASE_MAGIC, token, 24}; assert(call(434, in, 8) == IOCTL_ERROR); }
    assert(call(432, 0, 0) == IOCTL_ERROR && tx_ctx->running);
    { uint8 in[38] = {0}; in[1] = 3; assert(call(429, in, 38) == IOCTL_ERROR); assert(tx_ctx->task_token == token); }
    /* Legacy status remains 48-byte v1, slots estimate is bounded. */
    { uint32 out[12]; assert(call(433, out, 48) == 0); assert(out[0] == 0x3158544e && out[11] == 1 && out[3] > 0 && out[3] <= 18000); }
    assert(call(431, 0, 0) == 0); old_timer = timer_adds; i = allocations;
    tx_task_tx_now(tx_ctx); assert(timer_adds == old_timer && allocations == i);
    assert(renew(token, 24) == IOCTL_ERROR && call(430, 0, 0) == IOCTL_ERROR);
    status(s); assert(!s[4] && !s[5]);
    clear_context(); configure(3, 300, 18000); assert(tx_ctx->task_token != token);
    assert(call(430, 0, 0) == 0); assert(renew(token, 25) == IOCTL_ERROR);
    clear_context(); puts("PASS repeated renewals preserve cadence/context; status/token/sequence/stop contracts");
}
static void test_expiry_and_faults(void) {
    unsigned before;
    mock_regs.tsf_timerlow = 1234; configure(3, 300, 18000); assert(call(430,0,0)==0);
    due(); before = allocations;
    mock_regs.tsf_timerlow = tx_ctx->lease_deadline_tsf;
    assert(renew(tx_ctx->task_token,1)==IOCTL_ERROR);
    tx_task_tx_now(tx_ctx);
    assert(!tx_ctx->running && tx_ctx->stopped && tx_ctx->error == PIW_TX_ERROR_EXPIRED && allocations == before);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    before = allocations; mock_regs.tsf_timerlow = tx_ctx->lease_deadline_tsf;
    tx_task_tx_now(tx_ctx);
    assert(tx_ctx->error == PIW_TX_ERROR_EXPIRED && before == allocations);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    fail_alloc = 1; due(); before = allocations; due();
    assert(tx_ctx->error == PIW_TX_ERROR_ALLOC && !tx_ctx->running && allocations == before);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    mock_hw.up = 0; before = allocations; due();
    assert(tx_ctx->error == PIW_TX_ERROR_RADIO_DOWN && before == allocations);
    { uint32 out[8]; status(out); assert(!out[4] && !out[5] && out[6]==PIW_TX_ERROR_RADIO_DOWN); }
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    mock_regs.tsf_timerlow -= 5; before = allocations; tx_task_tx_now(tx_ctx);
    assert(tx_ctx->error == PIW_TX_ERROR_CLOCK_JUMP && before == allocations);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    mock_regs.tsf_timerlow += PIW_TX_LEASE_US + 1; before = allocations; tx_task_tx_now(tx_ctx);
    assert(tx_ctx->error == PIW_TX_ERROR_CLOCK_JUMP && before == allocations);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    during_alloc=stop_during_alloc; before=packets; due();
    assert(packets==before && discarded==1 && tx_ctx->stopped);
    assert(renew(tx_ctx->task_token,1)==IOCTL_ERROR);
    clear_context(); configure(3,300,18000); assert(call(430,0,0)==0);
    during_alloc=expire_during_alloc; before=packets; due();
    assert(packets==before && discarded==2 && tx_ctx->error==PIW_TX_ERROR_EXPIRED);
    clear_context(); puts("PASS expiry, stopped renew, allocation/radio failures, TSF jumps, allocation-stop/expiry interleavings");
}
static void test_wrap_and_skips(void) {
    unsigned i, before, first, token;
    mock_regs.tsf_timerlow = UINT32_MAX - 500000;
    configure(3,300,18000); assert(call(430,0,0)==0); token=tx_ctx->task_token;
    for(i=0;i<900;++i) due();
    assert(tx_ctx->running && tx_ctx->submitted == 900 && !tx_ctx->error);
    assert(renew(token,1)==0); first=tx_ctx->first_enqueue_tsf;
    tx_ctx->submitted = UINT32_MAX; due(); due();
    assert(tx_ctx->submitted==1 && tx_ctx->first_enqueue_tsf==first);
    /* Counter wrap does not trigger a new first timestamp. */
    before = packets; mock_regs.tsf_timerlow = tx_ctx->next_due + 2000000;
    tx_task_tx_now(tx_ctx);
    assert(packets == before+1 && tx_ctx->skipped == 600);
    assert((int)(tx_ctx->next_due - mock_regs.tsf_timerlow)>0);
    before=packets; tx_task_tx_now(tx_ctx); assert(packets==before);
    /* Delay while enqueueing: still one frame, skip missed slots, no burst. */
    advance_on_send = 10000000; before=packets; due();
    assert(packets == before+1 && tx_ctx->skipped == 3600 && tx_ctx->running);
    advance_on_send=0;
    /* Last valid sequence is accepted; sequence wrap is deliberately rejected. */
    assert(renew(token,UINT32_MAX)==0 && renew(token,1)==IOCTL_ERROR);
    clear_context();
    /* Generation wrap skips zero. */
    piw_task_generation=UINT32_MAX; configure(3,300,18000); assert(tx_ctx->task_token==1);
    clear_context(); puts("PASS TSF/counter wrap, late-slot bounded skipping, no catch-up burst");
}
static void test_finite_mode(void) {
    unsigned i;
    mock_regs.tsf_timerlow=0; configure(2,300,18000); assert(call(430,0,0)==0);
    for(i=0;i<18000;++i) due();
    assert(tx_ctx->submitted==18000 && !tx_ctx->running && !tx_ctx->repetitions && !tx_ctx->error);
    assert(renew(tx_ctx->task_token,1)==IOCTL_ERROR);
    clear_context(); configure(2,50,1500); assert(call(430,0,0)==0);
    for(i=0;i<1500;++i) due();
    assert(tx_ctx->submitted==1500 && !tx_ctx->running && tx_ctx->last_enqueue_tsf-tx_ctx->first_enqueue_tsf==1499*20000);
    clear_context(); puts("PASS legacy finite 300/50 Hz modes");
}
int main(void) {
    test_leases(); test_expiry_and_faults(); test_wrap_and_skips(); test_finite_mode();
    printf("Generated firmware native checks passed: packets=%u timer_adds=%u timer_frees=%u\n", packets, timer_adds, timer_frees);
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cc', required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    derivative = args.output / 'derivative'
    if derivative.exists():
        raise ValueError('Use a new test directory to keep previous native results')
    prepare(args.source, derivative)
    stubdir = args.output / 'native'
    stubdir.mkdir()
    (stubdir / 'native_stubs.h').write_text(STUBS, newline='\n')
    for name in ('firmware_version', 'wrapper', 'structs', 'helper', 'patcher', 'rates', 'sendframe', 'nexioctls'):
        (stubdir / (name + '.h')).write_text('#include "native_stubs.h"\n', newline='\n')
    harness = stubdir / 'test.c'
    harness.write_text(HARNESS, newline='\n')
    executable = (args.output / 'tx_task_native_test.exe').resolve()
    command = [args.cc, '-std=c11', '-O2', '-Wno-attributes', '-Wno-unknown-pragmas',
               '-I', str(stubdir), '-I', str(derivative / 'include'), str(harness), '-o', str(executable)]
    build = subprocess.run(command, text=True, capture_output=True)
    (args.output / 'build.log').write_text(build.stdout + build.stderr, newline='\n')
    if build.returncode:
        sys.stderr.write(build.stdout + build.stderr)
        return build.returncode
    run = subprocess.run([str(executable)], text=True, capture_output=True)
    (args.output / 'test.log').write_text(run.stdout + run.stderr, newline='\n')
    print(run.stdout, end='')
    if run.stderr:
        sys.stderr.write(run.stderr)
    return run.returncode


if __name__ == '__main__':
    sys.exit(main())
