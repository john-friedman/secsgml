from secsgml.secsgml.parse_sgml_submission import parse_sgml_submission
from time import time

start = time()
parse_sgml_submission(filepath='tests/0000891618-94-000021.txt',output_dir='results')
print('Time taken:', time()-start)