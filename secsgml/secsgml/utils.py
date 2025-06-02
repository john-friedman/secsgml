

def safe_decode_bytes(data,lower):
    """Decode bytes trying multiple encodings."""
    if not isinstance(data, bytes):
        return data
    
    # Try encodings in order
    for encoding in ['utf-8', 'latin-1']:
        try:
            return data.decode(encoding).lower() if lower else data.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Unable to decode bytes with utf-8 or latin-1 encodings")
    
    # Final fallback
    #return data.decode('utf-8', errors='replace')

# Convert bytes keys/values to strings for JSON serialization
def bytes_to_str(obj, lower=True):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # Handle dictionary keys
            if isinstance(k, bytes):
                new_key = safe_decode_bytes(k, lower)
            else:
                new_key = k
            # Recursively process values
            result[new_key] = bytes_to_str(v, lower)
        return result
    elif isinstance(obj, list):
        return [bytes_to_str(item, lower) for item in obj]
    elif isinstance(obj, bytes):
        decoded = safe_decode_bytes(obj, lower)
        return decoded.lower() if lower else decoded
    return obj