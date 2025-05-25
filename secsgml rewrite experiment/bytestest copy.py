# Show time in ms
from time import time
import mmap
import tarfile
import io
import os

def extract_documents(data):
    s = time()
    """Extract all document contents from mmap data"""
    start_tag = b'<DOCUMENT>'
    end_tag = b'</DOCUMENT>'
    
    documents = []
    pos = 0
    
    while True:
        start_pos = data.find(start_tag, pos)
        if start_pos == -1:
            break
        
        content_start = start_pos + len(start_tag)
        end_pos = data.find(end_tag, content_start)
        if end_pos == -1:
            break
        
        content = data[content_start:end_pos]
        documents.append(content)
        
        pos = end_pos + len(end_tag)
    
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
    s = time()
    parse_sgml_file('sgml/10k.txt')
    print(f"Total time taken: {(time() - s) * 1000:.2f} ms")