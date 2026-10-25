"""Prepare a bounded absolute-slot TX derivative; no device access or install.

Only local mode2 changes: delay denotes 50/300Hz, repetitions is a finite SLOT
budget. Mode3 keeps the same scheduler with a renewable 60-second lease.
Stock millisecond-timer modes remain available. No unverified microsecond
timer address is introduced. TSF uses declared BCM4366 register fields with
compile-time offsets; wl_add_timer uses the existing BCM4366 wrapper.
"""
import argparse
from pathlib import Path
import shutil


ABSOLUTE = r'''
/* BCM4366c0 target layout; fail compilation rather than borrow another chip's ABI. */
typedef char piw_wlc_regs_offset[__builtin_offsetof(struct wlc_info, regs) == 0x10 ? 1 : -1];
typedef char piw_tsf_low_offset[__builtin_offsetof(struct d11regs, tsf_timerlow) == 0x180 ? 1 : -1];
typedef char piw_lease_deadline_aligned[__builtin_offsetof(struct tx_context, lease_deadline_tsf) % 4 == 0 ? 1 : -1];
typedef char piw_context_aligned[__alignof__(struct tx_context) >= 4 ? 1 : -1];

/* Host-requested bounded test mode; TSF is observed at enqueue, not at airtime. */
uint32
piw_read_tsf(struct wlc_info *wlc)
{
    return ((volatile struct d11regs *)wlc->regs)->tsf_timerlow;
}

static uint32 piw_task_generation;

void
piw_init_context(struct tx_context *ctx)
{
    if (++piw_task_generation == 0)
        ++piw_task_generation;
    ctx->task_token = piw_task_generation;
}

void
piw_stop_absolute(struct tx_context *ctx, uint32 error)
{
    /* Sticky: neither a late renew nor a queued timer may restart this task. */
    ctx->stopped = 1;
    ctx->running = 0;
    if (error && !ctx->error)
        ctx->error = error;
}

static int
piw_lease_alive(struct tx_context *ctx, uint32 now)
{
    if (ctx->stopped || !ctx->running || ctx->error)
        return 0;
    /* Unsigned elapsed permits normal low-TSF wrap, rejects backwards/large jumps.
     * The scheduler normally runs every 3-4 ms. A full lease without a tick
     * cannot be recovered by a renewal that happens to arrive first. */
    if ((uint32)(now - ctx->last_tick_tsf) > PIW_TX_LEASE_US) {
        piw_stop_absolute(ctx, PIW_TX_ERROR_CLOCK_JUMP);
        return 0;
    }
    if ((int)(ctx->lease_deadline_tsf - now) <= 0) {
        piw_stop_absolute(ctx, PIW_TX_ERROR_EXPIRED);
        return 0;
    }
    return 1;
}

uint32
piw_lease_remaining_us(struct tx_context *ctx, uint32 now)
{
    int remaining;
    if (ctx->periodic != PIW_TX_LEASE_MODE || !ctx->running || ctx->stopped || ctx->error)
        return 0;
    remaining = (int)(ctx->lease_deadline_tsf - now);
    return remaining > 0 && (uint32)remaining <= PIW_TX_LEASE_US ? (uint32)remaining : 0;
}

int
piw_renew_lease(struct tx_context *ctx, uint32 token, uint32 sequence)
{
    uint32 now;
    if (!ctx || ctx->periodic != PIW_TX_LEASE_MODE || !sequence ||
        token != ctx->task_token || sequence <= ctx->renew_seq ||
        !ctx->wlc || !ctx->wlc->hw || !ctx->wlc->regs)
        return 0;
    if (!ctx->wlc->hw->up) {
        piw_stop_absolute(ctx, PIW_TX_ERROR_RADIO_DOWN);
        return 0;
    }
    now = piw_read_tsf(ctx->wlc);
    if (!piw_lease_alive(ctx, now))
        return 0;
    ctx->renew_seq = sequence;
    ++ctx->renewals;
    /* Single aligned store publishes the new lease. The timer only reads it;
     * renewal never changes running, next_due, fraction or timer ownership.
     * A concurrent stop remains sticky even if this store finishes afterwards. */
    __asm__ volatile ("" ::: "memory");
    ctx->lease_deadline_tsf = now + PIW_TX_LEASE_US;
    return 1;
}

uint32
piw_remaining_slots(struct tx_context *ctx, uint32 now)
{
    uint32 us;
    if (ctx->periodic != PIW_TX_LEASE_MODE)
        return ctx->repetitions;
    us = piw_lease_remaining_us(ctx, now);
    return (us / 1000000) * PIW_TX_LEASE_RATE +
           ((us % 1000000) * PIW_TX_LEASE_RATE + 999999) / 1000000;
}

static void
piw_next_slot(struct tx_context *ctx)
{
    if (ctx->delay == 50) {
        ctx->next_due += 20000;
    } else {
        ctx->next_due += 3333;
        if (++ctx->fraction == 3) {
            ++ctx->next_due;
            ctx->fraction = 0;
        }
    }
}

static void
piw_absolute_tick(struct tx_context *ctx)
{
    uint32 now, skip;
    int late;
    void *p;
    if (!ctx->running || ctx->stopped || !ctx->repetitions)
        return;
    if (!ctx->wlc->hw->up) {
        piw_stop_absolute(ctx, PIW_TX_ERROR_RADIO_DOWN);
        return;
    }
    now = piw_read_tsf(ctx->wlc);
    if (ctx->periodic == PIW_TX_LEASE_MODE && !piw_lease_alive(ctx, now))
        return;
    ctx->last_tick_tsf = now;
    late = (int)(now - ctx->next_due);
    if (late < 0) {
        wl_add_timer(ctx->wlc->wl, ctx->tx_task,
                     (ctx->next_due - now + 999) / 1000, 0);
        return;
    }
    if ((uint32)late > ctx->max_late_us)
        ctx->max_late_us = late;
    p = tx_task_get_frame(ctx);
    if (p == 0) {
        piw_stop_absolute(ctx, PIW_TX_ERROR_ALLOC); /* Never silently retry. */
        return;
    }
    if (ctx->periodic == PIW_TX_LEASE_MODE) {
        now = piw_read_tsf(ctx->wlc);
        if (!ctx->wlc->hw->up)
            piw_stop_absolute(ctx, PIW_TX_ERROR_RADIO_DOWN);
        if (!piw_lease_alive(ctx, now)) {
            /* Still owned here: expiry/stop during allocation must not submit. */
            pkt_buf_free_skb(ctx->wlc->osh, p, 0);
            return;
        }
    }
    if (!ctx->first_enqueue_seen) {
        ctx->first_enqueue_tsf = now;
        ctx->first_enqueue_seen = 1;
    }
    ctx->last_enqueue_tsf = now;
    sendframe(ctx->wlc, p, TX_DATA_FIFO, ctx->rate);
    ++ctx->submitted; /* Submission is NOT proof of successful air transmission. */
    if (ctx->periodic != PIW_TX_LEASE_MODE && --ctx->repetitions == 0) {
        ctx->running = 0;
        return;
    }
    piw_next_slot(ctx);
    now = piw_read_tsf(ctx->wlc);
    if (ctx->periodic == PIW_TX_LEASE_MODE) {
        if (!piw_lease_alive(ctx, now))
            return;
        /* Discard complete 10 ms / three-slot cycles in constant work, then
         * at most three residue slots. Fraction and absolute cadence survive. */
        if ((int)(now - ctx->next_due) >= 0) {
            skip = (now - ctx->next_due) / 10000;
            ctx->next_due += skip * 10000;
            ctx->skipped += skip * 3;
        }
    }
    /* Finite mode retains its original budget; lease mode has <=3 iterations. */
    while ((int)(ctx->next_due - now) <= 0) {
        ++ctx->skipped;
        if (ctx->periodic != PIW_TX_LEASE_MODE && --ctx->repetitions == 0) {
            ctx->running = 0;
            return;
        }
        piw_next_slot(ctx);
    }
    wl_add_timer(ctx->wlc->wl, ctx->tx_task,
                 (ctx->next_due - now + 999) / 1000, 0);
}

int
piw_start_absolute(struct tx_context *ctx)
{
    uint32 now;
    if (!ctx->wlc || !ctx->wlc->hw || !ctx->wlc->regs ||
        !ctx->wlc->hw->up || ctx->wlc->hw->corerev != 0x41 ||
        ctx->running || !ctx->repetitions || ctx->repetitions > 18000 ||
        (ctx->delay != 50 && ctx->delay != 300))
        return 0;
    if (ctx->periodic == PIW_TX_LEASE_MODE &&
        (ctx->stopped || ctx->delay != PIW_TX_LEASE_RATE ||
         ctx->repetitions != PIW_TX_LEASE_SLOTS))
        return 0;
    ctx->fraction = ctx->submitted = ctx->skipped = ctx->error = 0;
    ctx->stopped = ctx->first_enqueue_seen = 0;
    ctx->first_enqueue_tsf = ctx->last_enqueue_tsf = ctx->max_late_us = 0;
    now = piw_read_tsf(ctx->wlc);
    ctx->last_tick_tsf = now;
    ctx->next_due = now + 1000;
    if (ctx->periodic == PIW_TX_LEASE_MODE)
        ctx->lease_deadline_tsf = now + PIW_TX_LEASE_US;
    ctx->running = 1;
    wl_add_timer(ctx->wlc->wl, ctx->tx_task, 1, 0);
    return 1;
}
'''


def prepare(source, output):
    if output.exists():
        raise ValueError('Use a fresh derivative directory; retain the previous build')
    shutil.copytree(source, output)
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'router/tx_lease_protocol.h',
                    output / 'include/tx_lease_protocol.h')
    header = output / 'include/tx_task.h'
    h = header.read_text()
    h = h.replace('    uint8 frame[];', '''    uint32 next_due, fraction, submitted, skipped;
    volatile uint32 running, stopped;
    uint32 error;
    uint32 first_enqueue_tsf, last_enqueue_tsf, max_late_us;
    uint32 first_enqueue_seen, last_tick_tsf, task_token, renew_seq, renewals;
    volatile uint32 lease_deadline_tsf;
    uint8 frame[];''')
    # The context is private heap state, not a wire structure. Natural alignment
    # preserves the ARM layout and guarantees the deadline's 32-bit publication.
    h = h.replace('} __attribute__((packed));', '} __attribute__((aligned(4)));')
    h = h.replace('#define TX_DATA_FIFO 1', '#include <tx_lease_protocol.h>\n\n#define TX_DATA_FIFO 1')
    h = h.replace('#endif /*TX_TASK_H*/', '''int piw_start_absolute(struct tx_context *ctx);
uint32 piw_read_tsf(struct wlc_info *wlc);
void piw_init_context(struct tx_context *ctx);
void piw_stop_absolute(struct tx_context *ctx, uint32 error);
int piw_renew_lease(struct tx_context *ctx, uint32 token, uint32 sequence);
uint32 piw_lease_remaining_us(struct tx_context *ctx, uint32 now);
uint32 piw_remaining_slots(struct tx_context *ctx, uint32 now);

#endif /*TX_TASK_H*/''')
    header.write_text(h, newline='\n')
    path = output / 'src/tx_task.c'
    text = path.read_text()
    anchor = 'void\ntx_task_free(struct tx_context *ctx)'
    if anchor not in text:
        raise ValueError('Upstream TX context entry is missing')
    text = text.replace(anchor, ABSOLUTE + '\n' + anchor, 1)
    text = text.replace('    struct wlc_info *wlc = ctx->wlc;\n', '''    struct wlc_info *wlc = ctx->wlc;
    if (ctx->periodic == 2 || ctx->periodic == PIW_TX_LEASE_MODE) {
        piw_absolute_tick(ctx);
        return;
    }
''', 1)
    text = text.replace('    if (ctx->wlc != 0 && ctx->tx_task != 0) {', '''    piw_stop_absolute(ctx, 0);
    if (ctx->wlc != 0 && ctx->tx_task != 0) {''', 1)
    path.write_text(text, newline='\n')
    path = output / 'src/ioctl.c'
    text = path.read_text()
    anchor = '            /* disable minimum power consumption */'
    if anchor not in text:
        raise ValueError('Upstream TX initialization entry is missing')
    text = text.replace(anchor, '''            /* Never replace a live timer/context through a new config. */
            if (tx_ctx && tx_ctx->running)
                break;
            /* Local absolute modes are bounded and broadcast-data only. */
            if (params->periodic == 2 || params->periodic == PIW_TX_LEASE_MODE) {
                int i;
                if ((params->delay != 50 && params->delay != 300) ||
                    params->repetitions == 0 || params->repetitions > 18000 ||
                    frame_length < 24 || frame_length > 256 ||
                    params->frame[0] != 0x08 || params->frame[1] != 0)
                    break;
                for (i = 4; i < 10; ++i)
                    if (params->frame[i] != 0xff)
                        break;
                if (i != 10)
                    break;
                if (params->periodic == PIW_TX_LEASE_MODE &&
                    (params->delay != PIW_TX_LEASE_RATE ||
                     params->repetitions != PIW_TX_LEASE_SLOTS))
                    break;
            }
''' + anchor, 1)
    text = text.replace('            /* copy arguments to tx task context */',
                        '            piw_init_context(tx_ctx);\n\n            /* copy arguments to tx task context */', 1)
    anchor = '                tx_task_start(wlc, tx_ctx->tx_task, tx_ctx->delay, tx_ctx->periodic);'
    if anchor not in text:
        raise ValueError('Upstream TX start entry is missing')
    text = text.replace(anchor, '''                if (tx_ctx->periodic == 2 || tx_ctx->periodic == PIW_TX_LEASE_MODE) {
                    ret = piw_start_absolute(tx_ctx) ? IOCTL_SUCCESS : IOCTL_ERROR;
                    break;
                }
''' + anchor, 1)
    text = text.replace('                wl_del_timer(wlc->wl, tx_ctx->tx_task);',
                        '                piw_stop_absolute(tx_ctx, 0);\n                wl_del_timer(wlc->wl, tx_ctx->tx_task);', 1)
    text = text.replace('            /* remove task and clear context */', '''            /* Lease tasks require an explicit stop (or a completed fault stop).
             * tx_task_free still cancels/frees the timer before its context. */
            if (tx_ctx->periodic == PIW_TX_LEASE_MODE && tx_ctx->running)
                break;
            /* remove task and clear context */''', 1)
    anchor = '        default:\n'
    text = text.replace(anchor, '''        /* Diagnostic only: counters and ENQUEUE TSF, not per-frame air times. */
        case 433:
        {
            uint32 out[12], lo;
            if (tx_ctx == 0 || len < sizeof(out) || !wlc->regs || !wlc->hw->up)
                break;
            lo = piw_read_tsf(wlc);
            out[0] = 0x3158544e; out[1] = tx_ctx->running;
            out[2] = tx_ctx->delay; out[3] = piw_remaining_slots(tx_ctx, lo);
            out[4] = tx_ctx->submitted; out[5] = tx_ctx->skipped;
            out[6] = tx_ctx->error; out[7] = tx_ctx->max_late_us;
            out[8] = tx_ctx->first_enqueue_tsf; out[9] = tx_ctx->last_enqueue_tsf;
            out[10] = lo; out[11] = 1;
            memcpy(arg, out, sizeof(out));
            ret = IOCTL_SUCCESS;
            break;
        }
        case PIW_TX_LEASE_RENEW_IOCTL:
        {
            uint32 in[PIW_TX_LEASE_RENEW_WORDS];
            if (len != sizeof(in))
                break;
            memcpy(in, arg, sizeof(in)); /* Do not assume ioctl buffer alignment. */
            if (in[0] != PIW_TX_LEASE_MAGIC)
                break;
            ret = piw_renew_lease(tx_ctx, in[1], in[2]) ? IOCTL_SUCCESS : IOCTL_ERROR;
            break;
        }
        case PIW_TX_LEASE_STATUS_IOCTL:
        {
            uint32 out[PIW_TX_LEASE_STATUS_WORDS], lo;
            if (!tx_ctx || tx_ctx->periodic != PIW_TX_LEASE_MODE ||
                len < sizeof(out) || !wlc->regs || !wlc->hw)
                break;
            /* A down radio may have inaccessible core registers. Status can
             * still prove a sticky stop without touching TSF in that state. */
            lo = 0;
            if (wlc->hw->up)
                lo = piw_read_tsf(wlc);
            else if (tx_ctx->running)
                piw_stop_absolute(tx_ctx, PIW_TX_ERROR_RADIO_DOWN);
            out[0] = PIW_TX_LEASE_MAGIC; out[1] = PIW_TX_LEASE_VERSION;
            out[2] = tx_ctx->task_token; out[3] = tx_ctx->renew_seq;
            out[4] = (piw_lease_remaining_us(tx_ctx, lo) + 999) / 1000;
            out[5] = tx_ctx->running; out[6] = tx_ctx->error;
            out[7] = tx_ctx->renewals;
            memcpy(arg, out, sizeof(out));
            ret = IOCTL_SUCCESS;
            break;
        }
''' + anchor, 1)
    path.write_text(text, newline='\n')
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(prepare(a.source, a.output))
