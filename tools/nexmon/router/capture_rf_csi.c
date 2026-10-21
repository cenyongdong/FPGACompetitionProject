/* Bounded, passive CSI + owned-transmitter 802.11-header capture.
 * AF_PACKET timestamps are userspace arrival times, not RF timestamps.
 * CSI is kept in full; radio payloads and unrelated radio headers are not saved.
 * No wireless configuration, packet transmission or persistent installation.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <net/if.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t interrupted;
static void stop(int sig) { (void)sig; interrupted = 1; }
static unsigned le16(const unsigned char *p) { return p[0] | ((unsigned)p[1] << 8); }
static unsigned be16(const unsigned char *p) { return ((unsigned)p[0] << 8) | p[1]; }
static uint32_t getle32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static double mono(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    return t.tv_sec + t.tv_nsec / 1e9;
}
static int put32(FILE *f, uint32_t value) {
    unsigned char b[4] = {value, value >> 8, value >> 16, value >> 24};
    return fwrite(b, 1, 4, f) == 4 ? 0 : -1;
}
static FILE *new_pcap(const char *name, unsigned link) {
    FILE *f = fopen(name, "wbx");
    if (!f) return NULL;
    if (put32(f, 0xa1b2c3d4) || put32(f, 0x00040002) || put32(f, 0) ||
        put32(f, 0) || put32(f, 65535) || put32(f, link)) {
        fclose(f); return NULL;
    }
    return f;
}
static int write_frame(FILE *f, const struct timespec *t, const unsigned char *data,
                       size_t captured, size_t original) {
    return put32(f, (uint32_t)t->tv_sec) || put32(f, (uint32_t)(t->tv_nsec / 1000)) ||
           put32(f, (uint32_t)captured) || put32(f, (uint32_t)original) ||
           fwrite(data, 1, captured, f) != captured;
}
static int finish(FILE *f) {
    if (!f) return 0;
    int error = fflush(f);
    if (fsync(fileno(f))) error = 1;
    if (fclose(f)) error = 1;
    return error;
}
static unsigned number(const char *s, unsigned max) {
    char *end;
    errno = 0;
    unsigned long n = strtoul(s, &end, 10);
    return errno || !*s || *end || !n || n > max ? 0 : (unsigned)n;
}
static int mac(const char *s, unsigned char out[6]) {
    unsigned a[6]; char tail;
    if (sscanf(s, "%2x:%2x:%2x:%2x:%2x:%2x%c", &a[0], &a[1], &a[2], &a[3], &a[4], &a[5], &tail) != 6)
        return 0;
    for (int i = 0; i < 6; i++) out[i] = (unsigned char)a[i];
    return 1;
}
static int is_csi(const unsigned char *b, size_t n, const unsigned char tx[6]) {
    if (n < 14) return 0;
    size_t o = 14;
    unsigned type = be16(b + 12);
    for (int i = 0; i < 2 && (type == 0x8100 || type == 0x88a8); i++) {
        if (n < o + 4) return 0;
        type = be16(b + o + 2); o += 4;
    }
    if (type != 0x0800 || n < o + 20 || b[o] >> 4 != 4 || b[o + 9] != 17) return 0;
    size_t ihl = (b[o] & 15) * 4;
    if (ihl < 20 || be16(b + o + 6) & 0x3fff || n < o + ihl + 8 + 18) return 0;
    const unsigned char *udp = b + o + ihl, *payload = udp + 8;
    return be16(udp + 2) == 5500 && payload[0] == 0x11 && payload[1] == 0x11 &&
           !memcmp(payload + 4, tx, 6);
}
/* Return retained length, with the radio payload stripped. */
static size_t owned_header(const unsigned char *b, size_t n, unsigned hatype,
                           const unsigned char tx[6], const unsigned char bssid[6], unsigned *link) {
    size_t offset;
    if (hatype == 803) { /* ARPHRD_IEEE80211_RADIOTAP */
        if (n < 8 || b[0] != 0) return 0;
        offset = le16(b + 2); *link = 127;
        if (offset < 8 || offset > 512) return 0;
    } else if (hatype == 802) { /* ARPHRD_IEEE80211_PRISM */
        if (n < 8) return 0;
        offset = getle32(b + 4); *link = 119;
        if (offset < 8 || offset > 512) return 0;
    } else if (hatype == 801) { /* ARPHRD_IEEE80211 */
        offset = 0; *link = 105;
    } else return 0;
    if (n < offset + 24) return 0;
    const unsigned char *h = b + offset;
    unsigned fc = le16(h), type = (fc >> 2) & 3;
    if ((fc & 3) || (type != 0 && type != 2) || memcmp(h + 10, tx, 6)) return 0;
    unsigned ds = (fc >> 8) & 3;
    const unsigned char *network = ds == 1 ? h + 4 : ds == 2 ? h + 10 : h + 16;
    if (ds == 3 || memcmp(network, bssid, 6)) return 0;
    size_t header_length = 24;
    int qos = type == 2 && (fc & 0x0080);
    if (qos) header_length += 2;
    if ((qos || type == 0) && (fc & 0x8000)) header_length += 4;
    return n < offset + header_length ? 0 : offset + header_length;
}

int main(int argc, char **argv) {
    if (argc != 8) {
        fprintf(stderr, "usage: capture-rf-csi CSI_INTERFACE NEW_PREFIX SECONDS MAX_CSI MAX_RAW TX_MAC OWNED_BSSID\n");
        return 2;
    }
    unsigned seconds = number(argv[3], 20), csi_limit = number(argv[4], 20000), raw_limit = number(argv[5], 10000);
    unsigned csi_index = if_nametoindex(argv[1]);
    unsigned char tx[6], bssid[6];
    if (!seconds || !csi_limit || !raw_limit || !csi_index || !mac(argv[6], tx) || !mac(argv[7], bssid)) return 2;
    char csi_path[512], raw_path[512];
    if (snprintf(csi_path, sizeof(csi_path), "%s.csi.pcap", argv[2]) >= (int)sizeof(csi_path) ||
        snprintf(raw_path, sizeof(raw_path), "%s.headers.pcap", argv[2]) >= (int)sizeof(raw_path)) return 2;
    if (!access(csi_path, F_OK) || !access(raw_path, F_OK)) {
        fprintf(stderr, "Output already exists\n"); return 2;
    }
    int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (fd < 0) { perror("socket"); return 3; }
    int receive_buffer = 4 * 1024 * 1024;
    if (setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &receive_buffer, sizeof(receive_buffer))) {
        perror("receive buffer"); close(fd); return 3;
    }
    FILE *csi = new_pcap(csi_path, 1), *raw = NULL;
    if (!csi) { perror("new csi PCAP"); close(fd); return 3; }
    signal(SIGINT, stop); signal(SIGTERM, stop);
    double started = mono();
    int error = started < 0, raw_interface = 0;
    unsigned raw_link = 0, csi_count = 0, raw_count = 0;
    unsigned hatype1 = 0, hatype801 = 0, hatype802 = 0, hatype803 = 0, other = 0;
    size_t bytes = 24;
    unsigned char buffer[65535];
    while (!error && !interrupted && csi_count < csi_limit && raw_count < raw_limit && mono() < started + seconds) {
        struct pollfd p = {.fd = fd, .events = POLLIN};
        int ready = poll(&p, 1, 50);
        if (ready < 0) { if (errno == EINTR) continue; perror("poll"); error = 1; break; }
        if (!ready) continue;
        if (p.revents & (POLLERR | POLLHUP | POLLNVAL)) { error = 1; break; }
        struct sockaddr_ll from;
        socklen_t length = sizeof(from);
        ssize_t n = recvfrom(fd, buffer, sizeof(buffer), MSG_TRUNC, (struct sockaddr *)&from, &length);
        if (n < 0) { if (errno == EINTR) continue; perror("recvfrom"); error = 1; break; }
        if ((size_t)n > sizeof(buffer)) { error = 1; break; }
        if (from.sll_pkttype == PACKET_OUTGOING) continue;
        switch (from.sll_hatype) {
            case 1: hatype1++; break;
            case 801: hatype801++; break;
            case 802: hatype802++; break;
            case 803: hatype803++; break;
            default: other++; break;
        }
        struct timespec stamp;
        if (clock_gettime(CLOCK_REALTIME, &stamp)) { error = 1; break; }
        if ((unsigned)from.sll_ifindex == csi_index && is_csi(buffer, (size_t)n, tx)) {
            if (bytes + 16 + (size_t)n > 32u * 1024u * 1024u) { error = 1; break; }
            error = write_frame(csi, &stamp, buffer, (size_t)n, (size_t)n);
            csi_count++; bytes += 16 + (size_t)n;
        } else {
            unsigned link = 0;
            size_t keep = owned_header(buffer, (size_t)n, from.sll_hatype, tx, bssid, &link);
            if (!keep) continue;
            if (!raw) {
                raw = new_pcap(raw_path, link);
                if (!raw) { perror("new header PCAP"); error = 1; break; }
                raw_link = link; raw_interface = from.sll_ifindex; bytes += 24;
            }
            if (raw_link != link || raw_interface != from.sll_ifindex) continue;
            if (bytes + 16 + keep > 32u * 1024u * 1024u) { error = 1; break; }
            error = write_frame(raw, &stamp, buffer, keep, (size_t)n);
            raw_count++; bytes += 16 + keep;
        }
    }
    if (finish(csi)) error = 1;
    if (finish(raw)) error = 1;
    struct tpacket_stats stats = {0}; socklen_t stats_size = sizeof(stats);
    if (getsockopt(fd, SOL_PACKET, PACKET_STATISTICS, &stats, &stats_size)) error = 1;
    if (stats.tp_drops) error = 1;
    close(fd);
    char raw_name[IF_NAMESIZE] = "";
    if (raw_interface) if_indextoname((unsigned)raw_interface, raw_name);
    fprintf(stderr, "{\"csi_records\":%u,\"owned_radio_headers\":%u,\"raw_interface\":\"%s\",\"raw_linktype\":%u,"
                    "\"bytes\":%zu,\"elapsed_s\":%.6f,\"kernel_drops\":%u,\"interrupted\":%d,\"error\":%d,"
                    "\"incoming_hatype_counts\":{\"1\":%u,\"801\":%u,\"802\":%u,\"803\":%u,\"other\":%u}}\n",
            csi_count, raw_count, raw_name, raw_link, bytes, mono() - started, stats.tp_drops,
            (int)interrupted, error, hatype1, hatype801, hatype802, hatype803, other);
    return error ? 4 : interrupted ? 6 : 0;
}
