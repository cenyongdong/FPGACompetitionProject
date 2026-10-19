/* Bounded local UDP stimulus ledger. No radio or system configuration. */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
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
static uint64_t now(clockid_t id) {
    struct timespec t;
    if (clock_gettime(id, &t)) return 0;
    return (uint64_t)t.tv_sec * 1000000000u + t.tv_nsec;
}
static uint64_t little64(const unsigned char *p) {
    uint64_t n = 0;
    for (unsigned i = 0; i < 8; i++) n |= (uint64_t)p[i] << (8 * i);
    return n;
}
int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "usage: udp-stimulus-sink LOCAL_IP NEW.csv SECONDS\n"); return 2; }
    char *end;
    unsigned long seconds = strtoul(argv[3], &end, 10);
    if (!*argv[3] || *end || !seconds || seconds > 60) return 2;
    struct sockaddr_in address = {.sin_family = AF_INET, .sin_port = htons(39031)};
    if (inet_pton(AF_INET, argv[1], &address.sin_addr) != 1) return 2;
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) { perror("socket"); return 3; }
    int size = 1024 * 1024;
    if (setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size)) ||
        bind(fd, (struct sockaddr *)&address, sizeof(address))) {
        perror("socket setup"); close(fd); return 3;
    }
    int overflow = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_RXQ_OVFL, &overflow, sizeof(overflow))) {
        perror("overflow accounting"); close(fd); return 3;
    }
    FILE *f = fopen(argv[2], "wx");
    if (!f) { perror("new ledger"); close(fd); return 3; }
    signal(SIGINT, stop); signal(SIGTERM, stop);
    fprintf(f, "receive_mono_ns,receive_unix_ns,slot,sender_before_ns,sender_target_ns,source,bytes\n");
    uint64_t start = now(CLOCK_MONOTONIC), deadline = start + seconds * 1000000000ull;
    unsigned count = 0, foreign = 0, drops = 0;
    int error = start == 0;
    while (!error && !interrupted && count + foreign < 20000 && now(CLOCK_MONOTONIC) < deadline) {
        struct pollfd poller = {.fd = fd, .events = POLLIN};
        int ready = poll(&poller, 1, 50);
        if (ready < 0) { if (errno == EINTR) continue; error = 1; break; }
        if (!ready) continue;
        if (poller.revents & (POLLERR | POLLHUP | POLLNVAL)) { error = 1; break; }
        unsigned char data[2048], control[CMSG_SPACE(sizeof(uint32_t))];
        struct sockaddr_in source;
        struct iovec io = {.iov_base = data, .iov_len = sizeof(data)};
        struct msghdr message = {.msg_name = &source, .msg_namelen = sizeof(source),
            .msg_iov = &io, .msg_iovlen = 1, .msg_control = control, .msg_controllen = sizeof(control)};
        ssize_t n = recvmsg(fd, &message, MSG_TRUNC);
        uint64_t mono = now(CLOCK_MONOTONIC), real = now(CLOCK_REALTIME);
        if (n < 0) { if (errno == EINTR) continue; error = 1; break; }
        for (struct cmsghdr *c = CMSG_FIRSTHDR(&message); c; c = CMSG_NXTHDR(&message, c)) {
            if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SO_RXQ_OVFL && c->cmsg_len >= CMSG_LEN(sizeof(uint32_t)))
                memcpy(&drops, CMSG_DATA(c), sizeof(uint32_t));
        }
        if (n != 256 || memcmp(data, "CSI300V1", 8)) { foreign++; continue; }
        char ip[INET_ADDRSTRLEN];
        if (!mono || !real || !inet_ntop(AF_INET, &source.sin_addr, ip, sizeof(ip)) ||
            fprintf(f, "%llu,%llu,%llu,%llu,%llu,%s,%ld\n", (unsigned long long)mono,
                (unsigned long long)real, (unsigned long long)little64(data + 8),
                (unsigned long long)little64(data + 16), (unsigned long long)little64(data + 24), ip, (long)n) < 0) {
            error = 1; break;
        }
        count++;
    }
    if (count + foreign == 20000) error = 1;
    if (fflush(f) || fsync(fileno(f))) error = 1;
    if (fclose(f)) error = 1;
    close(fd);
    fprintf(stderr, "{\"datagrams\":%u,\"foreign\":%u,\"socket_drops\":%u,\"elapsed_s\":%.6f,\"interrupted\":%d,\"error\":%d}\n",
        count, foreign, drops, (now(CLOCK_MONOTONIC) - start) / 1e9, interrupted != 0, error);
    return error || drops ? 4 : interrupted ? 6 : count ? 0 : 5;
}
