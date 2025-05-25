from parse_sgml import parse_sgml_file_into_memory,write_sgml_file_to_tar
from time import time
import os

mydir=r"C:\Users\jgfri\OneDrive\Desktop\20090108.nc"
files = os.listdir(mydir)

s = time()
for file in files:
    # with open(f'{mydir}/{file}','rb') as f:
    #     content = f.read()
    write_sgml_file_to_tar(f'{mydir}/{file}','test.tar')
print(time()-s)