/* One naturally aligned volatile uint32_t device access per successful call.
 * No mapping, file access, SDK dependency, command construction or retry here.
 * The caller owns the valid mapping, range and lifetime of the address.
 */
#include <stdint.h>
#include <stddef.h>

#if defined(_WIN32)
#define MMIO_EXPORT __declspec(dllexport)
#else
#define MMIO_EXPORT __attribute__((visibility("default")))
#endif

static inline void before_access(void)
{
#if defined(__aarch64__)
    __asm__ __volatile__("dmb sy" ::: "memory");
#else
    /* Ordinary-memory host tests only. The released device build is AArch64. */
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
#endif
}

static inline void after_access(void)
{
#if defined(__aarch64__)
    __asm__ __volatile__("dsb sy" ::: "memory");
#else
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
#endif
}

MMIO_EXPORT uint32_t mmio32_abi(void)
{
    return UINT32_C(0x4d333201);
}

MMIO_EXPORT int mmio32_read32(const volatile uint32_t *address, uint32_t *out)
{
    uint32_t value;
    if (address == NULL || out == NULL ||
        ((uintptr_t)address & UINT32_C(3)) != 0 ||
        ((uintptr_t)out & UINT32_C(3)) != 0)
        return 22;
    before_access();
    value = *address;
    after_access();
    *out = value; /* Output is ordinary ctypes-owned CPU memory. */
    return 0;
}

MMIO_EXPORT int mmio32_write32(volatile uint32_t *address, uint32_t value)
{
    if (address == NULL || ((uintptr_t)address & UINT32_C(3)) != 0)
        return 22;
    before_access();
    *address = value;
    after_access();
    return 0;
}
