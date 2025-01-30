from secsgml import parse_sgml_submission
import os
import shutil
# delete previous results, using shutil
#shutil.rmtree('results', ignore_errors=True)



samples = os.listdir('samples')
samples = [os.path.join('samples', sample) for sample in samples]
for sample in samples:
    parse_sgml_submission(filepath=sample, output_dir='results') 