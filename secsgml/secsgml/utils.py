# Convert bytes keys/values to strings for JSON serialization
# also sends to lowercase
def bytes_to_str(obj):
    if isinstance(obj, dict):
        return {k.decode('utf-8').lower() if isinstance(k, bytes) else k: bytes_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [bytes_to_str(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8').lower()
    return obj

