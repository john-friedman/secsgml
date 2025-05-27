# Convert bytes keys/values to strings for JSON serialization
def bytes_to_str(obj, lower=True):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # Handle dictionary keys
            if isinstance(k, bytes):
                new_key = k.decode('utf-8').lower() if lower else k.decode('utf-8')
            else:
                new_key = k
            # Recursively process values
            result[new_key] = bytes_to_str(v, lower)
        return result
    elif isinstance(obj, list):
        return [bytes_to_str(item, lower) for item in obj]
    elif isinstance(obj, bytes):
        decoded = obj.decode('utf-8')
        return decoded.lower() if lower else decoded
    return obj