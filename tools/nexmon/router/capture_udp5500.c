/* Bounded Linux Ethernet capture for Nexmon UDP/5500. No radio configuration.
 * Writes original AF_PACKET frames to classic Ethernet PCAP. Outgoing copies
 * are excluded. Time limit uses CLOCK_MONOTONIC; PCAP uses receive wall time.
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
static unsigned be16(const unsigned char *p) { return ((unsigned)p[0] << 8) | p[1]; }
static double mono(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    return t.tv_sec + t.tv_nsec / 1e9;
}
static int le32(FILE *f, uint32_t n) {
    unsigned char b[4] = {n, n >> 8, n >> 16, n >> 24};
    return fwrite(b, 1, 4, f) == 4 ? 0 : -1;
}
static int selected(const unsigned char *b, size_t n) {
    if (n < 14) return 0;
    size_t o = 14;
    unsigned type = be16(b + 12);
    for (int i = 0; i < 2 && (type == 0x8100 || type == 0x88a8); i++) {
        if (n < o + 4) return 0;
        type = be16(b + o + 2); o += 4;
    }
    if (type != 0x0800 || n < o + 20 || b[o] >> 4 != 4 || b[o + 9] != 17) return 0;
    size_t ihl = (b[o] & 15) * 4;
    if (ihl < 20 || n < o + ihl + 8) return 0;
    if (be16(b + o + 6) & 0x3fff) return 0;
    unsigned port = be16(b + o + ihl + 2);
#ifdef NEXMON_DIAGNOSTIC_SIDECAR
    return port == 5500 || port == 5501;
#else
    return port == 5500;
#endif
}
static unsigned number(const char *s, unsigned maximum) {
    char *end;
    errno = 0;
    unsigned long value = strtoul(s, &end, 10);
    if (errno || !*s || *end || !value || value > maximum) return 0;
    return (unsigned)value;
}
int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: capture-udp5500 INTERFACE NEW.pcap SECONDS MAX_PACKETS\n");
        return 2;
    }
#ifdef NEXMON_DIAGNOSTIC_SIDECAR
    const unsigned maximum_packets = 40000; /* CSI plus independent metadata */
#else
    const unsigned maximum_packets = 20000;
#endif
    unsigned maximum_seconds = 60, packet_limit = maximum_packets;
#ifdef NEXMON_STREAM_CAPTURE
    /* Only the pipe mode can run longer. File captures retain their old caps. */
    if (!strcmp(argv[2], "-")) { maximum_seconds = 3600; packet_limit = 4000000; }
#endif
    unsigned seconds = number(argv[3], maximum_seconds), limit = number(argv[4], packet_limit);
    int continuous = 0;
#ifdef NEXMON_STREAM_CAPTURE
    /* No file growth: only a consumer-owned pipe may explicitly be unbounded
     * in time/count. Disconnect or SIGTERM still ends this capture instance. */
    continuous = !strcmp(argv[2], "-") && !strcmp(argv[3], "0") && !strcmp(argv[4], "0");
#endif
    unsigned index = if_nametoindex(argv[1]);
    if ((!continuous && (!seconds || !limit)) || !index) { fprintf(stderr, "invalid budget/interface\n"); return 2; }
    int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (fd < 0) { perror("socket"); return 3; }
    struct sockaddr_ll address = {.sll_family = AF_PACKET, .sll_protocol = htons(ETH_P_ALL), .sll_ifindex = index};
    if (bind(fd, (struct sockaddr *)&address, sizeof(address))) { perror("bind"); close(fd); return 3; }
    int streaming = 0;
#ifdef NEXMON_STREAM_CAPTURE
    streaming = !strcmp(argv[2], "-");
#endif
    /* A generation reset closes TCP. Preserve native drop/error counters on
     * EPIPE instead of losing the entire receipt to the default SIGPIPE. */
    if (streaming) signal(SIGPIPE, SIG_IGN);
    FILE *f = streaming ? stdout : fopen(argv[2], "wbx");
    if (!f) { perror("new output"); close(fd); return 3; }
    if (streaming) setvbuf(f, NULL, _IONBF, 0);
    int error = 0;
    error |= le32(f, 0xa1b2c3d4); error |= le32(f, 0x00040002);
    error |= le32(f, 0); error |= le32(f, 0); error |= le32(f, 65535); error |= le32(f, 1);
    signal(SIGINT, stop); signal(SIGTERM, stop);
    double start = mono(), deadline = start + seconds;
    if (start < 0) error = 1;
    unsigned long long count = 0;
    size_t bytes = 24;
    unsigned char buffer[65535];
    while (!error && !interrupted && (continuous || (count < limit && mono() < deadline))) {
        struct pollfd poller = {.fd = fd, .events = POLLIN};
        int ready = poll(&poller, 1, 50);
        if (ready < 0) { if (errno == EINTR) continue; perror("poll"); error = 1; break; }
        if (!ready) continue;
        if (poller.revents & (POLLERR | POLLHUP | POLLNVAL)) { error = 1; break; }
        struct sockaddr_ll from;
        socklen_t length = sizeof(from);
        ssize_t n = recvfrom(fd, buffer, sizeof(buffer), MSG_TRUNC, (struct sockaddr *)&from, &length);
        if (n < 0) { if (errno == EINTR) continue; perror("recvfrom"); error = 1; break; }
        if ((size_t)n > sizeof(buffer)) { fprintf(stderr, "oversized frame\n"); error = 1; break; }
        if (from.sll_pkttype == PACKET_OUTGOING || !selected(buffer, (size_t)n)) continue;
        if (!streaming && bytes + 16 + (size_t)n > 32u * 1024u * 1024u) {
            fprintf(stderr, "byte budget reached\n"); error = 1; break;
        }
        struct timespec timestamp;
        if (clock_gettime(CLOCK_REALTIME, &timestamp)) { error = 1; break; }
        error |= le32(f, (uint32_t)timestamp.tv_sec);
        error |= le32(f, (uint32_t)(timestamp.tv_nsec / 1000));
        error |= le32(f, (uint32_t)n); error |= le32(f, (uint32_t)n);
        if (fwrite(buffer, 1, (size_t)n, f) != (size_t)n) error = 1;
        count++; bytes += 16 + (size_t)n;
    }
    if (fflush(f) || (!streaming && fsync(fileno(f)))) error = 1;
    if (fclose(f)) error = 1;
    struct tpacket_stats statistics = {0};
    socklen_t statistics_size = sizeof(statistics);
    if (getsockopt(fd, SOL_PACKET, PACKET_STATISTICS, &statistics, &statistics_size)) error = 1;
    if (statistics.tp_drops) error = 1;
    close(fd);
    int budget_reached = !continuous && count == limit;
    fprintf(stderr, "{\"packets\":%llu,\"bytes\":%zu,\"elapsed_s\":%.6f,\"kernel_drops\":%u,\"interrupted\":%d,\"error\":%d,\"packet_budget_reached\":%d}\n",
            count, bytes, mono() - start, statistics.tp_drops, (int)interrupted, error, budget_reached);
    return error ? 4 : (interrupted ? 6 : (budget_reached ? 7 : (count ? 0 : 5)));
}
