import binascii

def decode(lines):
    """
    Decode UU-encoded content from list of strings
    Args:
        lines: list of strings containing UU-encoded data
    Returns:
        bytes: decoded data
    """
    # Find begin line
    for i, line in enumerate(lines):
        if line.startswith('begin'):
            start_idx = i + 1
            break
    else:
        raise ValueError('No valid begin line found')

    # Process content
    result = bytearray()
    
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped or stripped == 'end':
            break
            
        try:
            data = binascii.a2b_uu(stripped.encode())
        except binascii.Error:
            # Workaround for broken uuencoders
            nbytes = (((ord(stripped[0])-32) & 63) * 4 + 5) // 3
            data = binascii.a2b_uu(stripped[:nbytes].encode())
        
        result.extend(data)
    
    return bytes(result)