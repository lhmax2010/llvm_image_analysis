#!/usr/bin/env python3
"""Exercise lthor 3.4's archive_read_data API without devices or flashing."""
import ctypes as C
import ctypes.util
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
lib = C.CDLL(ctypes.util.find_library('archive'))
lib.archive_version_string.restype = C.c_char_p
lib.archive_read_new.restype = C.c_void_p
for name in ['archive_read_support_format_tar', 'archive_read_support_filter_gzip',
             'archive_read_free']:
    fn = getattr(lib, name)
    fn.argtypes = [C.c_void_p]
    fn.restype = C.c_int
lib.archive_read_open_filename.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
lib.archive_read_open_filename.restype = C.c_int
lib.archive_read_next_header.argtypes = [C.c_void_p, C.POINTER(C.c_void_p)]
lib.archive_read_next_header.restype = C.c_int
lib.archive_entry_size.argtypes = [C.c_void_p]
lib.archive_entry_size.restype = C.c_int64
lib.archive_read_data.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
lib.archive_read_data.restype = C.c_ssize_t
lib.archive_error_string.argtypes = [C.c_void_p]
lib.archive_error_string.restype = C.c_char_p
expected = json.loads((ROOT / 'evidence/sparse/summary.json').read_text())['image']
results = {'library': lib.archive_version_string().decode(),
           'scope': 'archive_read_data sequential host API; no lthor USB/device test',
           'cases': []}
for name in ['normal.tar', 'sparse.tar', 'sparse.tar.gz']:
    ar = lib.archive_read_new()
    try:
        assert lib.archive_read_support_format_tar(ar) == 0
        assert lib.archive_read_support_filter_gzip(ar) == 0
        assert lib.archive_read_open_filename(ar, str(ROOT / 'work/sparse' / name).encode(), 512) == 0
        entry = C.c_void_p()
        assert lib.archive_read_next_header(ar, C.byref(entry)) == 0
        logical = lib.archive_entry_size(entry)
        buf = C.create_string_buffer(1024 * 1024)
        h = hashlib.sha256()
        total = 0
        start = time.monotonic()
        while True:
            count = lib.archive_read_data(ar, buf, len(buf))
            if count < 0:
                raise RuntimeError(lib.archive_error_string(ar))
            if count == 0:
                break
            total += count
            h.update(buf.raw[:count])
        result = {'archive': name, 'member_logical_bytes': logical,
                  'sequential_bytes': total, 'sha256': h.hexdigest(),
                  'seconds': time.monotonic() - start}
        assert total == logical == expected['logical_bytes']
        assert h.hexdigest() == expected['sha256']
        results['cases'].append(result)
        print(json.dumps(result), flush=True)
    finally:
        lib.archive_read_free(ar)
(ROOT / 'evidence/sparse/libarchive-stream-results.json').write_text(json.dumps(results, indent=2) + '\n')
