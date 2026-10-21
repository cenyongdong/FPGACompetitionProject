"""Prepare an isolated BCM4366c0 diagnostic variant; never alter CSI/5500.

Input base.asm and csi.asm are the pinned upstream disassembly and its existing
CSI patch output. The 62-word internal RX header already reserves 124 bytes;
the extended synthetic header ends at byte 122. No RX allocation changes.
"""
from pathlib import Path
import argparse
import difflib


def prepare(cache: Path, preserve_tones=False):
    base = (cache / 'base.asm').read_text()
    asm = (cache / 'csi.asm').read_text()
    anchor = '\tmov\tSPARE4, [SHM(0x164c)]\n'
    assert asm.count(anchor) == 1
    asm = asm.replace(anchor, anchor + '''\
\t// Independent diagnostic words, within existing 62-word RX header.
\tmov\t[SHM(MAC_OFFSET)], SPARE4
\tmov\tSPARE4, [SHM(0x164e)]
\tmov\t0xffff, [SHM(0x1650)]
\txjl\tSPR_RXE_FRAMELEN, 32, diag_qos_done+
\tand\tSPARE4, 0x0300, SPARE4
\txjne\tSPARE4, 0x0300, diag_qos_threeaddr+
\txjl\tSPR_RXE_FRAMELEN, 38, diag_qos_done+
\tmov\t[SHM((MAC_OFFSET + 30))], SPARE4
\tjmp\tdiag_qos_store+
diag_qos_threeaddr:
\tmov\t[SHM((MAC_OFFSET + 24))], SPARE4
diag_qos_store:
\tmov\tSPARE4, [SHM(0x1650)]
diag_qos_done:
\tmov\t[0x878], SPARE4
\tmov\tSPARE4, [SHM(0x1652)]
\txadd\t[SHM(0x1654)], 1, [SHM(0x1654)]
''')
    delta = difflib.unified_diff(base.splitlines(True), asm.splitlines(True),
                                fromfile='a/ucode.asm', tofile='b/ucode.asm')
    patch = ''.join(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n'
                    for line in delta)
    (cache / 'metadata.ucode.patch').write_text(patch, newline='\n')
    src = (cache.parent / 'nexmon-rtac86u-20261017-r1/nexmon_csi/src/csi_extractor.c').read_text()
    src = src.replace('    uint16 chanspec;\n#else', '''    uint16 chanspec;
    uint16 diag_fc;
    uint16 diag_qos;
    uint16 diag_rx_tsf16;
    uint16 diag_event16;
#else''', 1)
    marker = 'struct int14 {'
    pos = src.index(marker)
    src = src[:pos] + '''// Diagnostic UDP/5501, little-endian payload, independent of CSI/5500.
// One record per completed core/stream; event16 and RX TSF are shared by
// all cores of one microcode dump. RX TSF is the hardware 16-bit RX timestamp,
// not host wall time. QoS is valid only for QoS data and != 0xffff.
struct diag_frame {
    struct ethernet_ip_udp_header hdrs;
    uint8 magic[4]; // NMD1
    uint16 version, length;
    uint8 src[6];
    uint16 seq, config, chanspec, fc, qos, rx_tsf16, event16;
} __attribute__((packed));

typedef char diag_header_fits[(34 + sizeof(struct d11csihdr) <= 124) ? 1 : -1];

static void emit_diag(struct wl_info *wl, struct d11csihdr *h)
{
    struct sk_buff *p = pkt_buf_get_skb(wl->wlc->osh, sizeof(struct diag_frame));
    if (!p) return;
    struct diag_frame *d = (struct diag_frame *)p->data;
    memcpy(d->magic, "NMD1", 4);
    d->version = 1;
    d->length = sizeof(struct diag_frame) - sizeof(struct ethernet_ip_udp_header);
    memcpy(d->src, h->src, 6);
    d->seq = h->seqcnt; d->config = h->csiconf; d->chanspec = h->chanspec;
    d->fc = h->diag_fc; d->qos = h->diag_qos;
    d->rx_tsf16 = h->diag_rx_tsf16; d->event16 = h->diag_event16;
    p->len = sizeof(struct diag_frame);
    skb_pull(p, sizeof(struct ethernet_ip_udp_header));
    prepend_ethernet_ipv4_udp_header(p);
    d = (struct diag_frame *)p->data;
    // UDP checksum is deliberately zero in the upstream IPv4 tunnel.
    d->hdrs.udp.src_port = 0x7d15; // htons(5501)
    d->hdrs.udp.dst_port = 0x7d15;
    wl->dev->chained->funcs->xmit(wl->dev, wl->dev->chained, p);
}

''' + src[pos:]
    anchor = '            p_csi = 0;\n        }\n        pkt_buf_free_skb'
    assert src.count(anchor) == 1
    src = src.replace(anchor, '            p_csi = 0;\n            emit_diag(wl, ucodecsifrm);\n        }\n        pkt_buf_free_skb')
    if preserve_tones:
        # Versioned independent sidecar only. The legacy CSI/5500 memcpy and
        # payload stay untouched; save the three original FFT words first.
        src = src.replace('uint16 seq, config, chanspec, fc, qos, rx_tsf16, event16;\n',
            'uint16 seq, config, chanspec, fc, qos, rx_tsf16, event16;\n'
            '    uint16 original_offset, original_count;\n    uint32 original_words[3];\n', 1)
        src = src.replace('static void emit_diag(struct wl_info *wl, struct d11csihdr *h)',
            'static void emit_diag(struct wl_info *wl, struct d11csihdr *h, uint16 offset, uint32 *original)')
        src = src.replace('memcpy(d->magic, "NMD1", 4);\n    d->version = 1;',
                          'memcpy(d->magic, "NMD2", 4);\n    d->version = 2;')
        anchor = '    d->rx_tsf16 = h->diag_rx_tsf16; d->event16 = h->diag_event16;\n'
        assert src.count(anchor) == 1
        src = src.replace(anchor, anchor + '    d->original_offset = offset; d->original_count = 3;\n'
            '    memcpy(d->original_words, original, sizeof(d->original_words));\n')
        anchor = '            memcpy(&udpfrm->csi_values[offset], phystatus, sizeof(phystatus));'
        assert src.count(anchor) == 1
        src = src.replace(anchor, '            uint32 diag_original[3];\n'
            '            memcpy(diag_original, &udpfrm->csi_values[offset], sizeof(diag_original));\n' + anchor)
        src = src.replace('emit_diag(wl, ucodecsifrm);','emit_diag(wl, ucodecsifrm, offset, diag_original);')
        src = src.replace('// Diagnostic UDP/5501, little-endian payload, independent of CSI/5500.',
            '// NMD2 UDP/5501: 44 bytes, with original words before PHY overwrite.\n'
            '// CSI/5500 and internal microcode RX header remain unchanged.')
    (cache / 'csi_extractor.c').write_text(src)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('cache', type=Path)
    p.add_argument('--preserve-tones', action='store_true', help='Emit versioned NMD2 with pre-overwrite FFT words')
    args = p.parse_args()
    prepare(args.cache, args.preserve_tones)


