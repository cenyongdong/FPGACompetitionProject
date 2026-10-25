"""Prepare a bounded absolute-slot TX derivative; no device access or install.

Only local mode2 changes: delay denotes 50/300Hz, repetitions is a finite SLOT
budget. Stock millisecond-timer modes remain available. No unverified microsecond
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

/* Host-requested bounded test mode; TSF is observed at enqueue, not at airtime. */
uint32
piw_read_tsf(struct wlc_info *wlc)
{
    return ((volatile struct d11regs *)wlc->regs)->tsf_timerlow;
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
    uint32 now;
    int late;
    void *p;
    if (!ctx->running || !ctx->repetitions)
        return;
    if (!ctx->wlc->hw->up) {
        ctx->error = 1;
        ctx->running = 0;
        return;
    }
    now = piw_read_tsf(ctx->wlc);
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
        ctx->error = 2; /* Allocation failure stops; never silently retry. */
        ctx->running = 0;
        return;
    }
    if (ctx->submitted == 0)
        ctx->first_enqueue_tsf = now;
    ctx->last_enqueue_tsf = now;
    sendframe(ctx->wlc, p, TX_DATA_FIFO, ctx->rate);
    ++ctx->submitted; /* Submission is NOT proof of successful air transmission. */
    if (--ctx->repetitions == 0) {
        ctx->running = 0;
        return;
    }
    piw_next_slot(ctx);
    now = piw_read_tsf(ctx->wlc);
    /* Skip elapsed slots rather than burst/catch up. Bound is the finite budget. */
    while ((int)(ctx->next_due - now) <= 0) {
        ++ctx->skipped;
        if (--ctx->repetitions == 0) {
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
    if (!ctx->wlc || !ctx->wlc->hw || !ctx->wlc->regs ||
        !ctx->wlc->hw->up || ctx->wlc->hw->corerev != 0x41 ||
        ctx->running || !ctx->repetitions || ctx->repetitions > 18000 ||
        (ctx->delay != 50 && ctx->delay != 300))
        return 0;
    ctx->fraction = ctx->submitted = ctx->skipped = ctx->error = 0;
    ctx->first_enqueue_tsf = ctx->last_enqueue_tsf = ctx->max_late_us = 0;
    ctx->next_due = piw_read_tsf(ctx->wlc) + 1000;
    ctx->running = 1;
    wl_add_timer(ctx->wlc->wl, ctx->tx_task, 1, 0);
    return 1;
}
'''


def prepare(source, output):
    if output.exists():
        raise ValueError('Use a fresh derivative directory; retain the previous build')
    shutil.copytree(source, output)
    header = output / 'include/tx_task.h'
    h = header.read_text()
    h = h.replace('    uint8 frame[];', '''    uint32 next_due, fraction, submitted, skipped, running, error;
    uint32 first_enqueue_tsf, last_enqueue_tsf, max_late_us;
    uint8 frame[];''')
    h = h.replace('#endif /*TX_TASK_H*/', 'int piw_start_absolute(struct tx_context *ctx);\nuint32 piw_read_tsf(struct wlc_info *wlc);\n\n#endif /*TX_TASK_H*/')
    header.write_text(h, newline='\n')
    path = output / 'src/tx_task.c'
    text = path.read_text()
    anchor = 'void\ntx_task_free(struct tx_context *ctx)'
    if anchor not in text:
        raise ValueError('Upstream TX context entry is missing')
    text = text.replace(anchor, ABSOLUTE + '\n' + anchor, 1)
    text = text.replace('    struct wlc_info *wlc = ctx->wlc;\n', '''    struct wlc_info *wlc = ctx->wlc;
    if (ctx->periodic == 2) {
        piw_absolute_tick(ctx);
        return;
    }
''', 1)
    path.write_text(text, newline='\n')
    path = output / 'src/ioctl.c'
    text = path.read_text()
    anchor = '            /* disable minimum power consumption */'
    if anchor not in text:
        raise ValueError('Upstream TX initialization entry is missing')
    text = text.replace(anchor, '''            /* Local absolute mode is finite, bounded and broadcast-data only. */
            if (params->periodic == 2) {
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
            }
''' + anchor, 1)
    anchor = '                tx_task_start(wlc, tx_ctx->tx_task, tx_ctx->delay, tx_ctx->periodic);'
    if anchor not in text:
        raise ValueError('Upstream TX start entry is missing')
    text = text.replace(anchor, '''                if (tx_ctx->periodic == 2) {
                    ret = piw_start_absolute(tx_ctx) ? IOCTL_SUCCESS : IOCTL_ERROR;
                    break;
                }
''' + anchor, 1)
    text = text.replace('                wl_del_timer(wlc->wl, tx_ctx->tx_task);',
                        '                tx_ctx->running = 0;\n                wl_del_timer(wlc->wl, tx_ctx->tx_task);', 1)
    anchor = '        default:\n'
    text = text.replace(anchor, '''        /* Diagnostic only: counters and ENQUEUE TSF, not per-frame air times. */
        case 433:
        {
            uint32 out[12], lo;
            if (tx_ctx == 0 || len < sizeof(out) || !wlc->regs || !wlc->hw->up)
                break;
            lo = piw_read_tsf(wlc);
            out[0] = 0x3158544e; out[1] = tx_ctx->running;
            out[2] = tx_ctx->delay; out[3] = tx_ctx->repetitions;
            out[4] = tx_ctx->submitted; out[5] = tx_ctx->skipped;
            out[6] = tx_ctx->error; out[7] = tx_ctx->max_late_us;
            out[8] = tx_ctx->first_enqueue_tsf; out[9] = tx_ctx->last_enqueue_tsf;
            out[10] = lo; out[11] = 1;
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
