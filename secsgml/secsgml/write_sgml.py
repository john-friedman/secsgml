import os
import mmap
import tarfile
import json
import copy
import io
from .parse_sgml import parse_sgml_content_into_memory
from .utils import bytes_to_str


def calculate_documents_locations_in_tar(metadata, documents):
    # Step 1: Add placeholder byte positions to get accurate size (10-digit padded)
    placeholder_metadata = copy.deepcopy(metadata)
    
    for file_num in range(len(documents)):
        if b'documents' in placeholder_metadata:
            placeholder_metadata[b'documents'][file_num][b'secsgml_start_byte'] = "9999999999"  # 10 digits
            placeholder_metadata[b'documents'][file_num][b'secsgml_end_byte'] = "9999999999"    # 10 digits
        else:
            placeholder_metadata[b'DOCUMENTS'][file_num][b'SECSGML_START_BYTE'] = "9999999999"  # 10 digits
            placeholder_metadata[b'DOCUMENTS'][file_num][b'SECSGML_END_BYTE'] = "9999999999"    # 10 digits
    
    # Step 2: Calculate size with placeholders
    placeholder_str = bytes_to_str(placeholder_metadata, lower=False)
    placeholder_json = json.dumps(placeholder_str).encode('utf-8')
    metadata_size = len(placeholder_json)
    
    # Step 3: Now calculate actual positions using this size
    current_pos = 512 + metadata_size
    current_pos += (512 - (current_pos % 512)) % 512
    
    # Step 4: Calculate real positions and update original metadata (10-digit padded)
    for file_num, content in enumerate(documents):
        start_byte = current_pos + 512
        end_byte = start_byte + len(content)
        
        if b'documents' in metadata:
            metadata[b'documents'][file_num][b'secsgml_start_byte'] = f"{start_byte:010d}"  # 10-digit padding
            metadata[b'documents'][file_num][b'secsgml_end_byte'] = f"{end_byte:010d}"      # 10-digit padding
        else:
            metadata[b'DOCUMENTS'][file_num][b'SECSGML_START_BYTE'] = f"{start_byte:010d}"  # 10-digit padding
            metadata[b'DOCUMENTS'][file_num][b'SECSGML_END_BYTE'] = f"{end_byte:010d}"      # 10-digit padding
        
        file_total_size = 512 + len(content)
        padded_size = file_total_size + (512 - (file_total_size % 512)) % 512
        current_pos += padded_size
    
    return metadata


def write_submission_to_tar(output_path,metadata,documents,standardize_metadata):
     # Write tar directly to disk
    with tarfile.open(output_path, 'w') as tar:

        # calculate document locations in tar
        metadata = calculate_documents_locations_in_tar(metadata, documents)
        
        # serialize metadata
        metadata_str  = bytes_to_str(metadata,lower=False)
        metadata_json = json.dumps(metadata_str).encode('utf-8')
        # save metadata
        tarinfo = tarfile.TarInfo(name='metadata.json')
        tarinfo.size = len(metadata_json)
        tar.addfile(tarinfo, io.BytesIO(metadata_json))

        for file_num, content in enumerate(documents, 0):
            if standardize_metadata:
                document_name = metadata[b'documents'][file_num][b'filename'] if metadata[b'documents'][file_num].get(b'filename') else metadata[b'documents'][file_num][b'sequence'] + b'.txt'
            # else use original uppercase name
            else:
                document_name = metadata[b'DOCUMENTS'][file_num][b'FILENAME'] if metadata[b'DOCUMENTS'][file_num].get(b'FILENAME') else metadata[b'DOCUMENTS'][file_num][b'SEQUENCE'] + b'.txt'
            document_name = document_name.decode('utf-8')
            tarinfo = tarfile.TarInfo(name=f'{document_name}')
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))

def write_sgml_file_to_tar(output_path, bytes_content=None, input_path=None,filter_document_types=[],keep_filtered_metadata=False,standardize_metadata=True):
    # Validate input arguments
    if bytes_content is None and input_path is None:
        raise ValueError("Either bytes_content or input_path must be provided")
    
    if bytes_content is not None and input_path is not None:
        raise ValueError("Cannot provide both bytes_content and input_path - choose one")
    
    # Validate output_path is provided
    if output_path is None:
        raise ValueError("output_path is required")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else 'output', exist_ok=True)
    
    # Get data either from file or direct content
    if input_path is not None:
        if not os.path.exists(input_path):
            raise ValueError("Filepath not found")
        
        with open(input_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
                # Extract all documents
                metadata, documents = parse_sgml_content_into_memory(bytes_content=data,filter_document_types=filter_document_types,keep_filtered_metadata=keep_filtered_metadata,standardize_metadata=standardize_metadata)
    else:
        # Use content directly
        metadata, documents = parse_sgml_content_into_memory(bytes_content=bytes_content, filter_document_types=filter_document_types,keep_filtered_metadata=keep_filtered_metadata,standardize_metadata=standardize_metadata)
    
    write_submission_to_tar(output_path,metadata,documents,standardize_metadata)


    


