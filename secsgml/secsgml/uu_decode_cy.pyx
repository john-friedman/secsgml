# cython: language_level=3
# uu_decode.pyx

import cython
from cpython.list cimport PyList_GET_SIZE, PyList_GET_ITEM
from cpython.bytes cimport PyBytes_AsString, PyBytes_Size, PyBytes_FromStringAndSize
from libc.string cimport memcpy
import binascii  # Import full module

@cython.boundscheck(False)
@cython.wraparound(False)
def decode(list lines):
    """
    Decode UU-encoded content from list of strings
    Args:
        lines: list of strings containing UU-encoded data
    Returns:
        bytes: decoded data
    """
    cdef:
        Py_ssize_t i, start_idx, n_lines
        str line, stripped
        bytearray result = bytearray()
        bytes data, encoded_line
        int nbytes
    
    # Find begin line
    n_lines = PyList_GET_SIZE(lines)
    for i in range(n_lines):
        line = <str>PyList_GET_ITEM(lines, i)
        if line.startswith('begin'):
            start_idx = i + 1
            break
    else:
        raise ValueError('No valid begin line found')

    # Process content
    for i in range(start_idx, n_lines):
        line = <str>PyList_GET_ITEM(lines, i)
        stripped = line.strip()
        if not stripped or stripped == 'end':
            break
            
        try:
            encoded_line = stripped.encode()
            data = binascii.a2b_uu(encoded_line)
        except Exception:  # Changed to catch any exception for broken uuencoders
            # Workaround for broken uuencoders
            nbytes = (((ord(stripped[0])-32) & 63) * 4 + 5) // 3
            data = binascii.a2b_uu(stripped[:nbytes].encode())
        
        result.extend(data)
    
    return bytes(result)