# Show time in ms
from time import time
import mmap
import tarfile
import io
import os

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

def parse_submission_metadata(content):

    return content


def parse_document_metadata(content):
    content = content.strip()
    keyvals = content.split(b'\n')
    
    doc_metadata_dict = {
        parts[0].lstrip(b'<'): parts[1] 
        for item in keyvals 
        for parts in [item.split(b'>', 1)] 
        if len(parts) == 2
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
        
        document_metadata_start = start_pos + len(b'<DOCUMENT>')
        document_metadata_end = data.find(b'<TEXT>', document_metadata_start)

        # add document metadata
        document_metadata.append(parse_document_metadata(data[document_metadata_start:document_metadata_end]))

        # set submission metadata if at start
        if pos == 0:
            submission_metadata = parse_submission_metadata(data[0:document_metadata_start])


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
    parse_sgml_file('sgml/10k.txt')