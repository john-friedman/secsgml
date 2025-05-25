import mmap
import tarfile
import io
import os
import re
import binascii

## REVISIT ##
sec_format_mappings = {
    b"conformed submission type": b"type",
    b"conformed period of report": b"period",
    b"filed as of date": b"filing-date",
    b"date as of change": b"date-of-filing-date-change",
    
    # Filer section - company data
    b"company conformed name": b"conformed-name",
    b"central index key": b"cik",
    b"standard industrial classification": b"assigned-sic",
    
    # Filer section - filing values
    b"sec act": b"act",
    b"sec file number": b"file-number",
    
    # Filer section - business address
    b"business phone": b"phone",

    # Filer section - former company
    b"date of name change": b"date-changed",    
}

# lets go for mutation approach
def transform_metadata(metadata):
    
    items = list(metadata.items())
    for key, value in items:
        
        key_lower = key.lower()
        standardized_key = sec_format_mappings.get(key_lower)

        if standardized_key is not None:
            cleaned_key = standardized_key
        else:
            cleaned_key = re.sub(rb'\s+',b'-',key_lower)

        # check is dict
        if isinstance(value,dict):
            # delete previous key
            metadata.pop(key)

            # check if not empty
            if value == {}:
                continue

            # assign new key
            metadata[cleaned_key] = value
            # clean value
            transform_metadata(value)
        # TODO check this works for multiple reporting owners
        elif isinstance(value,list):
            # delete previous key
            metadata.pop(key)
            # assign new key
            metadata[cleaned_key] = value
            for val in value:
                if isinstance(val,dict):
                    transform_metadata(val)
        else:
            # delete previous key
            metadata.pop(key)

            # special handling (need to check original key)
            if key_lower == b"standard industrial classification":
                sic_match = re.search(rb'\[(\d+)\]', value)
                value = sic_match.group(1)
            elif key_lower == b"act" and isinstance(value, bytes) and b"Act" in value:
                # Extract just the last two digits from "1934 Act"
                act_match = re.search(rb'(\d{2})(\d{2})\s+Act', value)
                if act_match:
                    value = act_match.group(2)
            # assign new key
            metadata[cleaned_key] = value
    

    return metadata

## REVISIT ##


# Note: *.pdf, *.gif, *.jpg, *.png,*.xlsx and *.zip files are uuencoded.
def should_decode_file(filename_bytes):
    filename = filename_bytes.lower()
    uuencoded_extensions = [b'.pdf', b'.gif', b'.jpg', b'.png', b'.xlsx', b'.zip']
    return any(filename.endswith(ext) for ext in uuencoded_extensions)
  
# I think we can get performance gains here
# UUencoded document text is 64 characters wide havent used that info
def decode_uuencoded_content(content):
    # Convert bytes to string lines for processing
    text_content = content.decode('utf-8', errors='replace')
    lines = text_content.splitlines()
    
    # Find begin line
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith('begin'):
            start_idx = i + 1
            break
    
    # if start_idx is None:
    #     return content  # Not UU-encoded, return original
    
    # Process content
    result = bytearray()
    
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped or stripped == 'end':
            break
            
        # should look at this for performance issues
        try:
            data = binascii.a2b_uu(stripped.encode())
        except binascii.Error:
            # Workaround for broken uuencoders
            if stripped:
                nbytes = (((ord(stripped[0])-32) & 63) * 4 + 5) // 3
                data = binascii.a2b_uu(stripped[:nbytes].encode())
            else:
                continue
        
        result.extend(data)
    
    return bytes(result)
    

# this adds like 3ms
# there are ways to optimize this
def clean_document_content(content):
    # Find first non-whitespace position
    start = 0
    while start < len(content) and content[start:start+1] in b' \t\n\r':
        start += 1
    
    # Check for opening tags at start
    if content[start:start+5] == b'<PDF>':
        content = content[start+5:]
    elif content[start:start+6] == b'<XBRL>':
        content = content[start+6:]
    elif content[start:start+5] == b'<XML>':
        content = content[start+5:]
    
    # Find last non-whitespace position
    end = len(content) - 1
    while end >= 0 and content[end:end+1] in b' \t\n\r':
        end -= 1
    end += 1
    
    # Check for closing tags at end
    if content[:end].endswith(b'</PDF>'):
        content = content[:end-6]
    elif content[:end].endswith(b'</XBRL>'):
        content = content[:end-7]
    elif content[:end].endswith(b'</XML>'):
        content = content[:end-6]
    
    return content.strip()

# have to be careful here, as some of the archive files have weird stuff like '>' in vars

# pass non empty line
def parse_keyval_line_archive(line):
    match = re.search(rb'[A-Z0-9]>', line)
    key = b''
    val = b''
    if match:
        split_pos = match.start()
        key = line[1:split_pos+1]
        val = line[split_pos+2:]
        
    return key, val

def parse_archive_submission_metadata(content):
    lines = content.strip().split(b'\n')
    submission_metadata_dict = {}
    current_dict = submission_metadata_dict
    stack = [submission_metadata_dict]
    
    for line in lines:
        line = line.lstrip()
        if not line:
            continue
            
        current_dict = stack[-1]
        
        key, value = parse_keyval_line_archive(line)
        # skip submission
        if key == b'SUBMISSION':
            continue
        
        if key:
            # Handle closing tags - pop from stack
            if key.startswith(b'/'):
                if len(stack) > 1:
                    stack.pop()
                continue
                
            if value:
                # Handle duplicate keys by converting to list
                if key in current_dict:
                    if not isinstance(current_dict[key], list):
                        # Convert existing value to list
                        current_dict[key] = [current_dict[key]]
                    current_dict[key].append(value)
                else:
                    current_dict[key] = value
            else:
                # Opening tag - create new dict and push to stack
                # Handle duplicate section keys
                new_section = {}
                if key in current_dict:
                    if not isinstance(current_dict[key], list):
                        # Convert existing section to list
                        current_dict[key] = [current_dict[key]]
                    current_dict[key].append(new_section)
                else:
                    current_dict[key] = new_section
                stack.append(new_section)
    
    return submission_metadata_dict

# I think this is fine for tab delim?
def parse_tab_submission_metadata(content):
    lines = content.strip().split(b'\n')
    submission_metadata_dict = {}
    current_dict = submission_metadata_dict
    stack = [submission_metadata_dict]
    
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
            
        indent_level = (len(line) - len(line.lstrip(b'\t')))
        
        while len(stack) > indent_level + 1:
            stack.pop()
            
        current_dict = stack[-1]
        
        if b':' in line:
            # Special handling for SEC-DOCUMENT and SEC-HEADER lines
            if line.strip().startswith(b'<SEC-DOCUMENT>') or line.strip().startswith(b'<SEC-HEADER>'):
                # Parse: <SEC-DOCUMENT>filename.txt : date
                tag_end = line.find(b'>')
                colon_pos = line.rfind(b' : ')
                
                if tag_end != -1 and colon_pos != -1:
                    tag_name = line[1:tag_end]  # Extract SEC-DOCUMENT or SEC-HEADER
                    filename = line[tag_end + 1:colon_pos].strip()
                    date = line[colon_pos + 3:].strip()
                    
                    # Transform key: SEC-DOCUMENT -> sec-document
                    key = tag_name.lower().replace(b'_', b'-')
                    value = filename + b' : ' + date
                else:
                    # Fallback to normal parsing if format is unexpected
                    key, value = line.strip().split(b':', 1)
                    key = key.strip()
                    value = value.strip()
            else:
                # Normal key:value parsing
                key, value = line.strip().split(b':', 1)
                key = key.strip()
                value = value.strip()
            
            if value:
                # Handle duplicate keys by converting to list
                if key in current_dict:
                    if not isinstance(current_dict[key], list):
                        # Convert existing value to list
                        current_dict[key] = [current_dict[key]]
                    current_dict[key].append(value)
                else:
                    current_dict[key] = value
            else:
                # Handle duplicate section keys
                new_section = {}
                if key in current_dict:
                    if not isinstance(current_dict[key], list):
                        # Convert existing section to list
                        current_dict[key] = [current_dict[key]]
                    current_dict[key].append(new_section)
                else:
                    current_dict[key] = new_section
                stack.append(new_section)
                
        elif b'>' in line:
            key, value = parse_keyval_line(line, b'>', b'<')
            # check that key is not "/SEC-HEADER"
            if key == b'/SEC-HEADER':
                continue
            if key:
                # Handle duplicate keys here too
                if key in current_dict:
                    if not isinstance(current_dict[key], list):
                        current_dict[key] = [current_dict[key]]
                    current_dict[key].append(value)
                else:
                    current_dict[key] = value

    return submission_metadata_dict

def parse_submission_metadata(content):
    submission_metadata = {}
    # detect type - needs first 3 chars
    
    if content[0:1] == b'-':
        submission_format = 'tab-privacy'
    elif content[0:3] == b'<SE':
        submission_format = 'tab-default'
    else:
        submission_format = 'archive'


    if submission_format == 'tab-privacy':
        # find first empty line
        privacy_msg_end = content.find(b'\n\n',0)
        privacy_msg_dict = {b'privacy-enhanced-message': content[0:privacy_msg_end]}
        content = content[privacy_msg_end+len(b'\n\n'):]


        submission_metadata = parse_tab_submission_metadata(content)

        submission_metadata = privacy_msg_dict |submission_metadata

        
    elif submission_format=='tab-default':
        submission_metadata  = parse_tab_submission_metadata(content)
    else:
        submission_metadata = parse_archive_submission_metadata(content)

    return submission_metadata


def parse_keyval_line(line, delimiter=b'>', strip_prefix=b'<'):
   parts = line.split(delimiter, 1)
   if len(parts) == 2:
       key = parts[0].lstrip(strip_prefix)
       value = parts[1]
       return key, value
   return None, None

def parse_document_metadata(content):
   content = content.strip()
   keyvals = content.split(b'\n')
   
   doc_metadata_dict = {
       key: value
       for line in keyvals
       for key, value in [parse_keyval_line(line)]
       if key is not None
   }
   
   return doc_metadata_dict


def parse_sgml_content_into_memory(bytes_content=None, filepath=None):
    # Validate input arguments
    if bytes_content is None and filepath is None:
        raise ValueError("Either bytes_content or filepath must be provided")
    
    if bytes_content is not None and filepath is not None:
        raise ValueError("Cannot provide both bytes_content and filepath - choose one")
    
    # Read data from file if filepath is provided
    if filepath is not None:
        with open(filepath, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
                return _parse_sgml_data(data)
    else:
        return _parse_sgml_data(bytes_content)

def _parse_sgml_data(data):
    documents = []
    submission_metadata = ""
    document_metadata = []

    pos = 0
    
    while True:
        start_pos = data.find(b'<DOCUMENT>', pos)
        if start_pos == -1:
            break

        # set submission metadata if at start
        if pos == 0:
            submission_metadata = parse_submission_metadata(data[0:start_pos])
            # standardize metadata
            submission_metadata = transform_metadata(submission_metadata)
        
        document_metadata_start = start_pos + len(b'<DOCUMENT>')
        document_metadata_end = data.find(b'<TEXT>', document_metadata_start)

        # add document metadata
        document_metadata.append(parse_document_metadata(data[document_metadata_start:document_metadata_end]))

        # add document content
        document_content_end = data.find(b'</TEXT>', document_metadata_end)
        
        content = data[document_metadata_end+len(b'<TEXT>'):document_content_end]

        # Check if this file should be UU-decoded
        filename_bytes = document_metadata[-1].get(b'FILENAME',False)
        if filename_bytes and should_decode_file(filename_bytes):
            content = decode_uuencoded_content(content)

        documents.append(clean_document_content(content))

        # find end of document
        pos = data.find(b'</DOCUMENT>', document_content_end)

    submission_metadata[b'documents'] = document_metadata
    
    return submission_metadata, documents

def write_sgml_file_to_tar(output_path, bytes_content=None, input_path=None):
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
                metadata, documents = parse_sgml_content_into_memory(bytes_content=data)
    else:
        # Use content directly
        metadata, documents = parse_sgml_content_into_memory(bytes_content=bytes_content)
    
    # Write tar directly to disk
    with tarfile.open(output_path, 'w') as tar:
        for file_num, content in enumerate(documents, 0):
            document_name = metadata[b'documents'][file_num][b'FILENAME'] if metadata[b'documents'][file_num].get(b'FILENAME') else metadata[b'documents'][file_num][b'SEQUENCE'] + b'.txt'
            document_name = document_name.decode('utf-8')
            tarinfo = tarfile.TarInfo(name=f'{document_name}')
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))


