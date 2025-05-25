# Show time in ms
from time import time
import mmap
import tarfile
import io
import os
import re

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
    match = re.search(rb'[A-Z]>', line)
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
        if key:
            # Handle closing tags - pop from stack
            if key.startswith(b'/'):
                if len(stack) > 1:
                    stack.pop()
                continue
                
            if value:
                current_dict[key] = value
            else:
                # Opening tag - create new dict and push to stack
                current_dict[key] = {}
                stack.append(current_dict[key])
    
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
           key, value = line.strip().split(b':', 1)
           key = key.strip()
           value = value.strip()
           
           if value:
               current_dict[key] = value
           else:
               current_dict[key] = {}
               stack.append(current_dict[key])
       elif b'>' in line:
            key, value = parse_keyval_line(line, b'>', b'<')
            # check that key is not "/SEC-HEADER"
            if key == b'/SEC-HEADER':
                continue
            if key:
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
        privacy_msg = ''
        # find first empty line
        privacy_msg_end = content.find(b'\n\n',0)
        content = content[privacy_msg_end+len(b'\n\n'):]
        submission_metadata = parse_tab_submission_metadata(content)
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


def extract_documents(data):
    s = time()
    """Extract all document contents from mmap data"""
    
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
        
        document_metadata_start = start_pos + len(b'<DOCUMENT>')
        document_metadata_end = data.find(b'<TEXT>', document_metadata_start)

        # add document metadata
        document_metadata.append(parse_document_metadata(data[document_metadata_start:document_metadata_end]))




        # add document content
        document_content_end = data.find(b'</TEXT>', document_metadata_end)
        
        content = data[document_metadata_end+len(b'<TEXT>'):document_content_end]

        documents.append(clean_document_content(content))

        # find end of document
        pos = data.find(b'</DOCUMENT>', document_content_end)
    
    elapsed_ms = (time() - s) * 1000
    print(f"Extracted {len(documents)} documents in {elapsed_ms:.2f} ms")
    return documents

def parse_sgml_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found")
        return
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    with open(filepath, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            # Extract all documents
            documents = extract_documents(data)
            s = time()
            
            if not documents:
                print("No documents found in the file")
                return
            
            # Write tar directly to disk
            with tarfile.open('output/documents.tar', 'w') as tar:
                for file_num, content in enumerate(documents, 1):
                    tarinfo = tarfile.TarInfo(name=f'{file_num}.txt')
                    tarinfo.size = len(content)
                    tar.addfile(tarinfo, io.BytesIO(content))
            
            elapsed_ms = (time() - s) * 1000
            print(f"Saved {len(documents)} documents to tar in {elapsed_ms:.2f} ms")

# Main execution
if __name__ == "__main__":
    parse_sgml_file(r"C:\Users\jgfri\OneDrive\Desktop\secsgml\secsgml rewrite experiment\sgml\tabdefault.txt")
    #parse_sgml_file(r"C:\Users\jgfri\OneDrive\Desktop\secsgml\sgml\tab-privacy.txt")