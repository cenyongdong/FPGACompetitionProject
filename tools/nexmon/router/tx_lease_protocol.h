#ifndef PIW_TX_LEASE_PROTOCOL_H
#define PIW_TX_LEASE_PROTOCOL_H

/* Local router <-> BCM4366 firmware control. All words are little endian.
 * No changes to injected Wi-Fi frames or RX CSI payloads. */
#define PIW_TX_LEASE_MAGIC 0x314c5854u
#define PIW_TX_LEASE_VERSION 1u
#define PIW_TX_LEASE_MODE 3u
#define PIW_TX_LEASE_RENEW_IOCTL 434
#define PIW_TX_LEASE_STATUS_IOCTL 435
#define PIW_TX_LEASE_SECONDS 60u
#define PIW_TX_LEASE_MS 60000u
#define PIW_TX_LEASE_US 60000000u
#define PIW_TX_LEASE_RATE 300u
#define PIW_TX_LEASE_SLOTS 18000u
#define PIW_TX_LEASE_RENEW_SECONDS 10u
#define PIW_TX_LEASE_RENEW_WORDS 3u
#define PIW_TX_LEASE_RENEW_BYTES 12u
#define PIW_TX_LEASE_STATUS_WORDS 8u
#define PIW_TX_LEASE_STATUS_BYTES 32u

enum piw_tx_lease_error {
    PIW_TX_ERROR_NONE = 0,
    PIW_TX_ERROR_RADIO_DOWN = 1,
    PIW_TX_ERROR_ALLOC = 2,
    PIW_TX_ERROR_EXPIRED = 3,
    PIW_TX_ERROR_CLOCK_JUMP = 4
};
enum piw_tx_lease_status_word {
    PIW_TX_LEASE_STATUS_MAGIC = 0,
    PIW_TX_LEASE_STATUS_VERSION = 1,
    PIW_TX_LEASE_STATUS_TOKEN = 2,
    PIW_TX_LEASE_STATUS_SEQUENCE = 3,
    PIW_TX_LEASE_STATUS_REMAINING_MS = 4,
    PIW_TX_LEASE_STATUS_RUNNING = 5,
    PIW_TX_LEASE_STATUS_ERROR = 6,
    PIW_TX_LEASE_STATUS_RENEWALS = 7
};

/* Configured but not started: token != 0, seq/remaining/running/error = 0.
 * 434 accepts strictly increasing nonzero sequences (no sequence wrap).
 * Rejected requests do not poison a healthy task or change its lease.
 * 431, expiry and errors stop permanently until a fresh 429 context. */
#endif
