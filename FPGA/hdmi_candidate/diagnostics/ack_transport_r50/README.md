# Synthetic ACK transport comparison

Files: `host.mjs` (local Node), `board_client.py` (board Python standard library). They do not load SDK/MMIO/models or read inference archives. Every record is 60,784 synthetic bytes, marker `SYNTHACK`, sequence1..64, remaining bytes0xa5. Host validates and completes the local file-write callback before ACK(u64); client sends confirm(u64); host parses confirmation before the next record. TCP_NODELAY is true at both application endpoints. These are benchmark bytes, not production results or a protocol replacement.

Host binds only127.0.0.1:39481, at most90s. Client binds nothing, connects127.0.0.1:39481 through the reverse forward, at most15s/64rounds, at most30Hz with no catch-up burst. Connection/timeout failure stops, without reconnect/retry. Each run requires fresh host/client output directories.

Root owns all SSH authentication, board commands and process handles. Use the already verified memory-only NativeAskpass.exe launcher and pinned known_hosts entry, with StrictHostKeyChecking=yes, HostKeyAlgorithms=ssh-ed25519, PubkeyAuthentication=no, PreferredAuthentications=password, NumberOfPasswordPrompts=1, ConnectTimeout=5, ExitOnForwardFailure=yes. Do not put the password in argv/environment/files. Both implementations must run outside the sandbox, with exactly the same forward `-N -R 127.0.0.1:39481:127.0.0.1:39481`, destination, pinned key and helper.

- Windows executable: `C:/Windows/System32/OpenSSH/ssh.exe`; disable user config with `-F NUL`.
- Existing Git executable: `C:/Program Files/Git/usr/bin/ssh.exe`; equivalent null config is `-F /dev/null` under MSYS. Do not use NUL as an ordinary MSYS filename. Other forwarding/auth/keepalive arguments remain identical. The executable paths are verified locally; the Git MSYS runtime requires an unsandboxed context even for `-V`.

For each implementation separately, start local host and wait for its ready.json, start that one reverse forward with the established memory launcher, then let root execute the uploaded client once on the board. Never run both forwards against the same port concurrently. Stop only the saved host/forward handles belonging to that comparison after collecting exit status; the host normally exits itself after confirmation64.

```powershell
node D:/FPGACompetitionProject/.local/hdmi-ack-transport-20261024-r50/host.mjs D:/FPGACompetitionProject/.local/hdmi-ack-transport-20261024-r50/windows-host
```

Root uploads board_client.py, then invokes (fresh output directory with an existing parent):

```text
python3 /root/hdmi-ack-transport-20261024-r50/board_client.py /root/hdmi-ack-transport-20261024-r50/windows-client
```

Use `git-host`/`git-client` for the second comparison, without changing the synthetic payload or sequence rules. `client-timing.jsonl` contains same-board-clock send/ACK durations; `host-timing.jsonl` contains same-host-clock successful-write/ACK/confirmation timestamps. Never subtract absolute timestamps across machines. result.json records actual completed counts and native errors; 64rounds/exit0 are required at both ends. Successful OS write callback is not per-record fsync. Transport-only results do not prove AI/HDMI throughput, physical display or D47 repair.
