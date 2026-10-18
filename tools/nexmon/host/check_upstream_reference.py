"""Compare the Python unpacker with upstream C on a defined int32-safe range.

The original MATLAB routine rescales to int32 and has undefined shifts outside
that range. This comparison does not claim equivalence outside the safe range.
"""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys

from csi_verify import parse_payload, pcap_udp, unpack_acphy


def main(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    original = source / 'utils/matlab/unpack_float.c'
    text = original.read_text()
    function = text[text.index('void unpack_float_acphy'):text.index('void mexFunction')]
    c_file = output / 'reference_unpack.c'
    c_file.write_text('#include <stdint.h>\ntypedef uint32_t uint32_T;\n'
                      'typedef int32_t int32_T;\ntypedef int8_t int8_T;\n'
                      '#define k_tof_unpack_sgn_mask (1u<<31)\n' + function)
    library = output / 'reference_unpack.so'
    subprocess.run(['gcc', '-shared', '-fPIC', '-O2', '-o', str(library), str(c_file)], check=True)
    routine = ctypes.CDLL(str(library)).unpack_float_acphy
    routine.argtypes = [ctypes.c_int] * 7 + [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_int32)]
    rng = random.Random(20261017)
    compared = 0
    for nman, nexp in [(9, 5), (12, 6)]:
        shift = 10 + (1 << (nexp - 1))
        for nfft in [64, 128, 256]:
            for _ in range(16):
                words = []
                for _ in range(nfft):
                    real = rng.randrange(-(1 << (nman - 1)) + 1, 1 << (nman - 1))
                    imag = rng.randrange(-(1 << (nman - 1)) + 1, 1 << (nman - 1))
                    exponent = rng.randrange(-(1 << (nexp - 1)), 21 - shift)
                    words.append((abs(real) << (nexp + nman)) | (abs(imag) << nexp)
                                 | (exponent & ((1 << nexp) - 1))
                                 | ((real < 0) << (nexp + 2 * nman - 1))
                                 | ((imag < 0) << (nexp + nman - 1)))
                packed = (ctypes.c_uint32 * nfft)(*words)
                actual = (ctypes.c_int32 * (2 * nfft))()
                routine(10, 0, 0, 1, nman, nexp, nfft, packed, actual)
                decoded = unpack_acphy(words, nman, nexp)
                for index, value in enumerate(decoded):
                    assert math.ldexp(value.real, shift) == actual[2 * index]
                    assert math.ldexp(value.imag, shift) == actual[2 * index + 1]
                    compared += 1
    sample = source / 'utils/matlab/example.pcap'
    sample_records = [parse_payload(data, 256, 'legacy18') for _, data in pcap_udp(sample)]
    assert len(sample_records) == 4
    assert sorted((r['core'], r['stream']) for r in sample_records) == [(0, 0), (0, 1), (1, 0), (1, 1)]
    for record in sample_records:
        assert all(math.isfinite(abs(v)) for v in unpack_acphy(record['words'], 9, 5))
    result = dict(passed=True, compared_complex_values=compared,
                  upstream_c_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                  upstream_pcap_sha256=hashlib.sha256(sample.read_bytes()).hexdigest(),
                  upstream_pcap_records=4, upstream_pcap_chip='BCM4358 reference, not RT-AC86U',
                  limitation='C comparison limited to defined int32-safe shifts; no radio test')
    (output / 'upstream-reference.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    main(*sys.argv[1:])
