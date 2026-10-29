#pragma once
#include <unistd.h>

namespace pose180_pipeline {
// State belongs to the SDK owner thread. A timeout/exception never clears it.
// Only the normal synchronous contract or the existing final-output proof may
// mark a submitted operation complete. This does not reset/cancel any hardware.
class ReleaseGuard {
    const char* pending_ = nullptr;
public:
    void begin(const char* stage) noexcept { pending_ = stage; }
    void complete() noexcept { pending_ = nullptr; }
    bool permitted() const noexcept { return pending_ == nullptr; }
    const char* stage() const noexcept { return pending_ ? pending_ : "idle"; }

    template<class Notify> void retain_if_unproved(Notify&& notify) const noexcept {
        if (permitted()) return;
        try { notify(stage()); } catch (...) {}
        static constexpr char message[] = "SDK_RELEASE_BLOCKED: retain owner; no automatic reset/retry\n";
        const auto diagnostic_bytes=::write(STDERR_FILENO, message, sizeof(message)-1);
        (void)diagnostic_bytes; // A full/broken diagnostic pipe cannot permit release.
        // Keep the process, inherited exclusive lease, tensors and device alive.
        // TERM/INT/HUP request stop but cannot prove an in-flight DMA has ended.
        // No further SDK access is made. External controlled recovery is needed.
        for (;;) ::sleep(1);
    }
};
}
