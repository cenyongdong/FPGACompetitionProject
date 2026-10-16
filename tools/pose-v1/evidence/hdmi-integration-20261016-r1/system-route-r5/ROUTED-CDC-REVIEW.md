# Routed HDMI CDC review

This review permits local candidate generation for the already approved staged test. It does not turn the whole design's generic CDC report into a pass.

The 107 CDC-1 rows all originate in payload_hold. The 207 CDC-15 rows are handshake-controlled payload/response captures. The source holds command data until a two-stage synchronized response returns; the target holds its response until the next accepted request. Request/response toggles use two ASYNC_REG stages. Actual data limits remain 5ns/10ns; 96 command-driven CE endpoints separately retain 5ns, worst slack +0.856ns. No data or CE constraint was changed for this review.

The three CDC-6 buses are registered binary-to-Gray pointers/counter with two receiving stages. They retain source-period max-delay and skew constraints; all three routed skew checks pass. Neither binary counter buses nor unregistered Gray conversion are directly sampled.

CDC-10/12 reset rows terminate at the three intentional asynchronous assertion / three-stage local release chains. Only their nine CLR pins are cut. Eighty FIFO functional state resets were traced to their own-domain release chain in synthesis; functional recovery/removal remain timed and routed global setup/hold have no failures. Original negative recovery/removal reports are preserved.

The other CDC-10 rows are combinational run/idle flags entering two ASYNC_REG stages. Running is running && !stopping; START arms at a frame boundary, STOP/fault prevents subsequent requests and drains accepted reads. Idle requires stopping and no running/frame/waiting/reader activity. CSR idle is diagnostic only and cannot authorize frame release. Bars cannot be re-enabled after the first START. Release requires the atomic mailbox snapshot and stopped ID, never a separately synchronized idle bit. The r8 full-pixel/underflow/drain/stopped-pixel-clock tests remain the applicable logic evidence; this is not a measured MTBF or arbitrary reset-sequence guarantee.

All eight OSERDES CLK/CLKDIV pins use serial_raw/pixel_clk from the same MMCM output through adjacent BUFIO/BUFR resources. REQP-1580 is absent. REQP-1577 feedback buffering warning remains active: internal relative clock checks and real-model PHY simulation pass, while external eye/monitor operation still require actual board testing. No new check severity or timing exception was added.
