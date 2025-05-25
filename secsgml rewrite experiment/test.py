# test.py
import time
import mmap
from sgmltest import extract_documents_fast as extract_documents

def extract_documents_python(data):
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
       documents.append(data[content_start:end_pos])
       pos = end_pos + len(end_tag)
   
   return documents

def test(filepath):
   with open(filepath, 'rb') as f:
       with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            # Cython  
           start = time.perf_counter()
           cy_docs = extract_documents(bytes(data))
           cy_time = (time.perf_counter() - start) * 1000
           # Python
        #    start = time.perf_counter()
        #    py_docs = extract_documents_python(data)
        #    py_time = (time.perf_counter() - start) * 1000
           

           
           #print(f"Python:  {py_time:.2f}ms, {len(py_docs)} docs")
           print(f"Cython:  {cy_time:.2f}ms, {len(cy_docs)} docs") 
           #print(f"Speedup: {py_time/cy_time:.2f}x")

test('sgml/10k.txt')