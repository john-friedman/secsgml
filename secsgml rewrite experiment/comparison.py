from secsgml import parse_sgml_submission
from time import time
s= time()
parse_sgml_submission(filepath='sgml/10k.txt',output_dir='outputsecsgml')
print(f"Time taken: {time() - s} seconds")