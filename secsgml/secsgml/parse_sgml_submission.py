import os
import uu
from io import BytesIO
from itertools import dropwhile

# oh. we also need to handle document metadata

def detect_uu(first_line):
    """Detect if the document is uuencoded"""
    first_line = first_line.strip()
    if first_line.startswith('begin'):
        return True
    else:
        return False
    
def clean_lines(lines):
    """Clean lines by removing leading and trailing whitespace as well as special tags"""
    # Find first non-empty line and remove prefix
    lines = list(dropwhile(lambda x: not x.strip(), lines))
    
    # Handle special tags if present
    if lines and lines[0].strip() in ['<PDF>', '<XBRL>', '<XML>']:
        # Find matching closing tag
        tag = lines[0].strip()[1:-1]  # Extract tag name without brackets
        end_tag = f'</{tag}>'

        # Remove opening tag
        lines = lines[1:]
        
        # Keep only content up to closing tag if found
        try:
            last_idx = next(i for i, line in enumerate(reversed(lines)) 
                          if line.strip() == end_tag)
            lines = lines[:-last_idx-1]
        except StopIteration:
            pass  # No closing tag found
            
    return lines

def parse_text_tag_contents(lines, output_path):
    """Write the contents of a <TEXT> tag to a file"""
    lines = clean_lines(lines)

    content = '\n'.join(lines)
    # Check for UUencoded file
    if detect_uu(lines[0]):
        # handle uuencoded file
        with BytesIO(content.encode()) as input_file:
                uu.decode(input_file, output_path, quiet=True)
    else:
        # write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

# LOOK HERE AND REWRITE

def get_documents(lines):
    documents = []
    current_doc = []
    in_document = False
    
    for line in lines:
        if line.strip() == '<DOCUMENT>':
            in_document = True
            # Skip the DOCUMENT tag itself
            continue
        elif line.strip() == '</DOCUMENT>':
            in_document = False
            # Join and add the completed document
            documents.append(''.join(current_doc))
            current_doc = []
        elif in_document:
            current_doc.append(line)
            
    return documents

def detect_submission_type(first_line):
    if first_line.startswith('<SUBMISSION>'):
        return 'dashed-default'
    elif first_line.startswith('-----BEGIN PRIVACY-ENHANCED MESSAGE-----'):
        return 'tab-privacy'
    elif first_line.startswith('<SEC-DOCUMENT>'):
        return 'tab-default'
    else:
        raise ValueError('Unknown submission type')
    

def parse_sgml_submission(content = None, filepath = None,output_dir = None):
    if not filepath and not content:
        raise ValueError("Either filepath or content must be provided")
    
    os.makedirs(output_dir, exist_ok=True)

    # we will read the accension number, remove the dashes and use it to create the folder

    # If content not provided, read from file
    if content is None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    # Split into Lines
    lines = content.splitlines(keepends=True)

    # Split lines into header and documents
    header_start = lines.index('<DOCUMENT>')
    header = lines[:header_start]
    
    # documents
    documents = get_documents(lines[header_start:])


            