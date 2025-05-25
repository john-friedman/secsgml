from parse_sgml import parse_sgml_file_into_memory,write_sgml_file_to_tar
from secsgml import parse_sgml_submission_into_memory
from time import time
import os
import json

mydir=r"C:\Users\jgfri\OneDrive\Desktop\20090108.nc"
files = os.listdir(mydir)

def convert_bytes_keys(obj):
    if isinstance(obj, dict):
        return {
            (k.decode('utf-8') if isinstance(k, bytes) else k): convert_bytes_keys(v) 
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_bytes_keys(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return obj

s = time()
for file in files:
    file  = r"C:\Users\jgfri\OneDrive\Desktop\secsgml\secsgml rewrite experiment\sgml\multiplefilers.txt"
    with open(f'{file}','rb') as f:
        content = f.read()
    metadata,docs = parse_sgml_file_into_memory(content)
    # save metadata to test.json from bytes
    with open('test.json', 'w') as f:
        json.dump(convert_bytes_keys(metadata), f, indent=4)
    break
print(time()-s)

metadata,_ = parse_sgml_submission_into_memory(content=content.decode('utf-8'))
with open('compare.json', 'w') as f:
    json.dump(metadata,f,indent=4)