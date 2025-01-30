from secsgml.secsgml.parse_sgml_submission import parse_sgml_submission
from time import time

start = time()
parse_sgml_submission(filepath='tests/000095017025003585.sgml',output_dir='results')
print('Time taken:', time()-start)