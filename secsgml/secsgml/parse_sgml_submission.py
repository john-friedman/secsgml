import os
import uu
from io import BytesIO
from itertools import dropwhile
import json

SUBMISSION_TYPES = {
    '<SUBMISSION>': 'dashed-default',
    '-----BEGIN PRIVACY-ENHANCED MESSAGE-----': 'tab-privacy', 
    '<SEC-DOCUMENT>': 'tab-default'
}

def detect_submission_type(first_line):
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
                tag, text = line.split(':')
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

def parse_text_tag_contents(lines, output_path):
    """Write the contents of a <TEXT> tag to a file"""
    lines = clean_lines(lines)
    content = '\n'.join(lines)
    
    if detect_uu(lines[0]):
        with BytesIO(content.encode()) as input_file:
            uu.decode(input_file, output_path, quiet=True)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)  # More efficient than writelines for joined content


            
def parse_document_metadata(lines):
    """Parse metadata between first line and first <TEXT> tag"""
    return {
        line.split('>')[0][1:].lower(): line.split('>')[1].strip()
        for line in lines
    }
def get_documents(lines):
    """Returns list of tuples containing start and end indices for each document"""
    doc_marker = '<DOCUMENT>\n'  # Include newline to avoid string operations
    doc_end = '</DOCUMENT>\n'
    
    doc_ranges = []
    start_idx = None
    
    for i, line in enumerate(lines):
        if line == doc_marker:
            start_idx = i + 1  # Start after the marker
        elif line == doc_end and start_idx is not None:
            doc_ranges.append((start_idx, i))
            start_idx = None
            
    return doc_ranges

def parse_sgml_submission(content=None, filepath=None, output_dir=None):
    if not filepath and not content:
        raise ValueError("Either filepath or content must be provided")
    
    os.makedirs(output_dir, exist_ok=True)

    # If content not provided, read from file
    if content is None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    # Split into Lines - strip newlines here since we'll add them back when needed
    lines = [line.rstrip('\n') for line in content.splitlines()]

    # Detect submission type
    submission_type = detect_submission_type(lines[0])

    # grab header metadata lines
    first_document_idx = next(i for i, line in enumerate(lines) if line == '<DOCUMENT>')
    header_lines = lines[:first_document_idx]
    lines = lines[first_document_idx:]

    # Parse header metadata
    header_metadata = parse_header_metadata(header_lines, submission_type)

    # Get accession number and create directory
    if submission_type == 'dashed-default':
        accession_number = header_metadata['accession-number'].replace('-','')
    elif submission_type == 'tab-default' or submission_type == 'tab-privacy':
        accession_number = header_metadata['accession number'].replace('-','')

    accession_dir = os.path.join(output_dir, accession_number)
    os.makedirs(accession_dir, exist_ok=True)

    # Process documents using the new range-based approach
    metadata = header_metadata
    metadata['documents'] = []
    doc_ranges = get_documents([line + '\n' for line in lines])  # Add newlines just for finding ranges
    
    for start_idx, end_idx in doc_ranges:
        document_lines = lines[start_idx:end_idx]
        
        # Find TEXT tags - match without newlines now
        text_tag_idx = next(i for i, line in enumerate(document_lines) if line == '<TEXT>')
        text_tag_end_idx = next(i for i, line in enumerate(document_lines[text_tag_idx:], text_tag_idx) 
                               if line == '</TEXT>')
        
        # Split document sections
        document_metadata_lines = document_lines[:text_tag_idx]
        text_lines = document_lines[text_tag_idx+1:text_tag_end_idx]
        
        # Parse document metadata
        document_metadata = parse_document_metadata(document_metadata_lines)
        
        # Add to main metadata
        metadata['documents'].append(document_metadata)
        
        # Process text contents - add newlines between lines but not at end
        text_content = '\n'.join(text_lines)
        output_filename = document_metadata.get('filename', document_metadata['sequence'] + '.txt')
        document_path = os.path.join(accession_dir, output_filename)
        
        # Use original parse_text_tag_contents with properly formatted content
        parse_text_tag_contents(text_content.splitlines(), document_path)

    # Write metadata
    metadata_path = os.path.join(accession_dir, 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)