"""Raw CSI transport; deliberately contains no model preprocessing/inference."""
import struct
import numpy as np

MAGIC = b'PIWCSI1\0'
HEADER = struct.Struct('<8sIIQQ')
SHAPE = (3, 3, 30, 20)  # receiver, antenna, subcarrier, sample
PAYLOAD_BYTES = 3 * 3 * 30 * 20 * 2 * 8


def load_mat(path):
    import h5py
    with h5py.File(path, 'r') as handle:
        raw = handle['csi_out'][()]
    if raw.shape != (20, 30, 3, 3) or not {'real', 'imag'}.issubset(raw.dtype.names or ()):
        raise ValueError('Unexpected raw CSI shape/dtype: ' + str(path))
    return np.asarray((raw['real'] + 1j * raw['imag']).transpose(3, 2, 1, 0), dtype=np.complex128)


def encode_window(csi, frame_id, source_time_ns=0):
    if csi.shape != SHAPE or not np.isfinite(csi).all():
        raise ValueError('Raw CSI must have shape (3,3,30,20) and be finite')
    pairs = np.stack((csi.real, csi.imag), axis=-1).astype('<f8')
    return HEADER.pack(MAGIC, 1, PAYLOAD_BYTES, frame_id, source_time_ns) + pairs.tobytes()
