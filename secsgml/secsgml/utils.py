import json
import copy

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


def calculate_documents_locations_in_tar(metadata):
    # Step 1: Add placeholder byte positions to get accurate size (10-digit padded)
    placeholder_metadata = copy.deepcopy(metadata)

    # Check for bytes
    is_bytes = any(term in placeholder_metadata for term in [b'documents', b'DOCUMENTS'])

    if is_bytes:
        # Check if using lowercase or uppercase keys
        isLower = b'documents' in placeholder_metadata
        if isLower:
            doc_key = b'documents'
            size_key = b'secsgml_size_bytes'
            start_key = b'secsgml_start_byte'
            end_key = b'secsgml_end_byte'
        else:
            doc_key = b'DOCUMENTS'
            size_key = b'SECSGML_SIZE_BYTES'
            start_key = b'SECSGML_START_BYTE'
            end_key = b'SECSGML_END_BYTE'
    else:
        # Check if using lowercase or uppercase keys
        isLower = 'documents' in placeholder_metadata
        if isLower:
            doc_key = 'documents'
            size_key = 'secsgml_size_bytes'
            start_key = 'secsgml_start_byte'
            end_key = 'secsgml_end_byte'
        else:
            doc_key = 'DOCUMENTS'
            size_key = 'SECSGML_SIZE_BYTES'
            start_key = 'SECSGML_START_BYTE'
            end_key = 'SECSGML_END_BYTE'

    document_length = len(metadata[doc_key])
    
    for file_num in range(document_length):
        placeholder_metadata[doc_key][file_num][start_key] = "9999999999"  # 10 digits
        placeholder_metadata[doc_key][file_num][end_key] = "9999999999"  # 10 digits

    # Step 2: Calculate size with placeholders
    placeholder_str = bytes_to_str(placeholder_metadata, lower=False)
    placeholder_json = json.dumps(placeholder_str).encode('utf-8')
    metadata_size = len(placeholder_json)
    
    # Step 3: Now calculate actual positions using this size
    current_pos = 512 + metadata_size
    current_pos += (512 - (current_pos % 512)) % 512
    
    # Step 4: Calculate real positions and update original metadata (10-digit padded)
    for file_num in range(document_length):
        size_bytes = metadata[doc_key][file_num][size_key]  # Get size from original metadata
        start_byte = current_pos + 512
        end_byte = start_byte + size_bytes

        metadata[doc_key][file_num][start_key] = f"{start_byte:010d}"  # Update original metadata
        metadata[doc_key][file_num][end_key] = f"{end_byte:010d}"     # Update original metadata
        
        file_total_size = 512 + size_bytes
        padded_size = file_total_size + (512 - (file_total_size % 512)) % 512
        current_pos += padded_size
    
    return metadata
