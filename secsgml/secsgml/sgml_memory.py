from .uu_decode_cy import decode as uu_decode
from itertools import dropwhile

def detect_submission_type(first_line):
    SUBMISSION_TYPES = {
        '<SUBMISSION>': 'dashed-default',
        '-----BEGIN PRIVACY-ENHANCED MESSAGE-----': 'tab-privacy', 
        '<SEC-DOCUMENT>': 'tab-default'
    }
    for marker, type_ in SUBMISSION_TYPES.items():
        if first_line.startswith(marker):
            return type_
    raise ValueError('Unknown submission type')

def parse_header_metadata(lines, submission_type):
    """We pass in first line to line before first <DOCUMENT> tag"""
    header_metadata = {}
    
    if submission_type == 'dashed-default':
        current_dict = header_metadata
        stack = [(header_metadata, None)]  # (dict, tag) pairs
        
        for i, line in enumerate(lines):
            tag, text = line.split('>')
            tag = tag[1:].lower()  # Remove '<' and convert to lowercase
            text = text.strip()
            
            # Handle closing tags
            if tag.startswith('/'):
                tag = tag[1:]  # Remove the '/'
                if stack and stack[-1][1] == tag:
                    stack.pop()
                    current_dict = stack[-1][0] if stack else header_metadata
                continue
                
            # Look ahead to check if this tag has a closing tag
            next_lines = lines[i+1:]
            is_paired = any(l.strip().lower().startswith(f'</{tag}>') for l in next_lines)
            
            if is_paired:
                nested_dict = {}
                if tag in current_dict:
                    if isinstance(current_dict[tag], list):
                        current_dict[tag].append(nested_dict)
                    else:
                        current_dict[tag] = [current_dict[tag], nested_dict]
                else:
                    current_dict[tag] = nested_dict
                stack.append((nested_dict, tag))
                current_dict = nested_dict
            elif text:
                if tag in current_dict:
                    if isinstance(current_dict[tag], list):
                        current_dict[tag].append(text)
                    else:
                        current_dict[tag] = [current_dict[tag], text]
                else:
                    current_dict[tag] = text

    else:  # tab-default or tab-privacy
        current_dict = header_metadata
        stack = [(0, header_metadata)]

        if submission_type == 'tab-privacy':
            privacy_msg = []
            for i, line in enumerate(lines):
                if line.strip() == '-----BEGIN PRIVACY-ENHANCED MESSAGE-----':
                    j = i + 1
                    while j < len(lines) and not (lines[j].strip() == '' or 
                          ('<' in lines[j] and any(c.isupper() for c in lines[j][lines[j].find('<')+1:]))):
                        privacy_msg.append(lines[j].strip())
                        j += 1
                    header_metadata['privacy-enhanced-message'] = '\n'.join(privacy_msg)
                    lines = lines[j:]
                    break

        for line in lines:
            if not line.strip():
                continue
                
            indent = len(line) - len(line.lstrip())
            
            try:
                tag, text = line.split('>')
                tag = tag[1:].lower().strip()
                if tag.startswith('/'):
                    continue
            except:
                tag, text = line.split(':',1)
                tag = tag.strip().lower()
            
            text = text.strip()
            
            while len(stack) > 1 and stack[-1][0] >= indent:
                stack.pop()
            
            current_dict = stack[-1][1]
            
            if text:
                if tag in current_dict:
                    if isinstance(current_dict[tag], list):
                        current_dict[tag].append(text)
                    else:
                        current_dict[tag] = [current_dict[tag], text]
                else:
                    current_dict[tag] = text
            else:
                while len(stack) > 1 and stack[-1][0] == indent:
                    stack.pop()
                    
                nested_dict = {}
                if tag in current_dict:
                    if isinstance(current_dict[tag], list):
                        current_dict[tag].append(nested_dict)
                    else:
                        current_dict[tag] = [current_dict[tag], nested_dict]
                else:
                    current_dict[tag] = nested_dict
                
                stack.append((indent, nested_dict))
                current_dict = nested_dict
    
    return header_metadata    

def detect_uu(first_line):
    """Detect if the document is uuencoded"""
    return first_line.strip().startswith('begin')

def clean_lines(lines):
    """Clean lines by removing leading/trailing whitespace and special tags"""
    lines = list(dropwhile(lambda x: not x.strip(), lines))
    if not lines:
        return lines
        
    SPECIAL_TAGS = {'<PDF>', '<XBRL>', '<XML>'}
    first_line = lines[0].strip()
    if first_line in SPECIAL_TAGS:
        tag = first_line[1:-1]  # Remove < >
        end_tag = f'</{tag}>'
        
        # Find closing tag position, default to end if not found
        try:
            end_pos = len(lines) - next(i for i, line in enumerate(reversed(lines)) 
                        if line.strip() == end_tag) - 1
        except StopIteration:
            end_pos = len(lines)
            
        lines = lines[1:end_pos]
            
    return lines

def process_text_content(lines):
    """Process the contents of a <TEXT> tag and return as bytes"""
    lines = clean_lines(lines)
    if not lines:
        return b''
    elif detect_uu(lines[0]):
        # Pass lines directly to decoder
        return uu_decode(lines)  # uu_decode would take list of strings
    else:
        # For regular text content, encode to bytes
        return '\n'.join(lines).encode('utf-8')

def parse_document_metadata(lines):
    """Parse metadata between first line and first <TEXT> tag"""
    metadata = {}
    current_key = None
    
    for line in lines:
        if line.startswith('<'):
            if '>' in line:
                current_key, value = line.split('>', 1)
                metadata[current_key[1:].lower()] = value.strip()
        elif current_key:  # Continuation of previous value
            metadata[current_key[1:].lower()] += ' ' + line.strip()
            
    return metadata

class DocumentIndex:
    def __init__(self):
        self.document_positions = []  # start, end positions
        self.text_positions = []      # start, end positions
        self.header_end = 0
        self.text_leftovers = {}  

def build_document_index(lines):
    """Just indexes document positions - no metadata handling"""
    index = DocumentIndex()
    
    doc_start = None
    text_start = None
    
    # Find first document to mark header end
    for i, line in enumerate(lines):
        if line == '<DOCUMENT>':
            index.header_end = i
            break
    
    # Index all document and text positions 
    for i, line in enumerate(lines):
        if line == '<DOCUMENT>':
            doc_start = i
        elif line == '</DOCUMENT>':
            if doc_start is not None:
                index.document_positions.append((doc_start, i))
                doc_start = None
        elif line == '<TEXT>':
            text_start = i
        elif '</TEXT>' in line:
            # Check if next non-empty line is </DOCUMENT>
            next_line = None
            j = i + 1
            while j < len(lines) and not next_line:
                if lines[j].strip():
                    next_line = lines[j].strip()
                j += 1
            
            if next_line == '</DOCUMENT>' and text_start is not None:
                if '</TEXT>' != line:
                    leftover = line.split('</TEXT>')[0]
                    index.text_leftovers[i] = leftover
                index.text_positions.append((text_start, i))
                text_start = None
    
    return index

def parse_sgml_submission_into_memory(content=None, filepath=None):
    """Parse SGML submission and return (metadata, documents)
    
    Returns:
        tuple: (metadata dict, list of document contents)
        The document contents are all bytes objects
    """
    if not filepath and not content:
        raise ValueError("Either filepath or content must be provided")

    # Read content if not provided
    if content is None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    lines = content.splitlines()
    
    # Detect submission type
    submission_type = detect_submission_type(lines[0])
    
    # Get document structure index
    doc_index = build_document_index(lines)
    
    # Parse header metadata
    header_lines = lines[:doc_index.header_end]
    metadata = parse_header_metadata(header_lines, submission_type)
    
    # Process documents using indexed positions
    documents = []
    
    for doc_start, doc_end in doc_index.document_positions:
        # Find corresponding text section for this document
        text_start, text_end = next(
            (start, end) for start, end in doc_index.text_positions 
            if start > doc_start and end < doc_end
        )
        
        # Extract document metadata and add to header metadata
        doc_metadata = parse_document_metadata(lines[doc_start+1:text_start])
        
        # Process text contents
        text_lines = lines[text_start+1:text_end]
        
        # If there's leftover content at the end
        if text_end in doc_index.text_leftovers:
            text_lines.append(doc_index.text_leftovers[text_end])
            
        # Process content and add to documents list
        content = process_text_content(text_lines)
        documents.append(content)

        # Add document metadata to the metadata dictionary
        if 'documents' not in metadata:
            metadata['documents'] = []
        metadata['documents'].append(doc_metadata)
    
    return metadata, documents