from secsgml import parse_sgml_submission
import os
import shutil
import filecmp
from pathlib import Path
from time import time

def compare_folders(original_path, new_path):
    # Convert paths to Path objects for easier handling
    original = Path(original_path)
    new = Path(new_path)
    
    # Get all files recursively in both directories
    original_files = {str(f.relative_to(original)): f 
                     for f in original.rglob('*') if f.is_file()}
    new_files = {str(f.relative_to(new)): f 
                 for f in new.rglob('*') if f.is_file()}
    
    # Check for files that exist in original but not in new
    for rel_path in original_files:
        if rel_path not in new_files:
            print(f"File missing in new folder: {original_files[rel_path]}")
    
    # Check for files that exist in new but not in original
    for rel_path in new_files:
        if rel_path not in original_files:
            print(f"Extra file in new folder: {new_files[rel_path]}")
    
    # Compare contents of files that exist in both folders
    for rel_path in set(original_files.keys()) & set(new_files.keys()):
        if not filecmp.cmp(original_files[rel_path], new_files[rel_path], shallow=False):
            print(f"Content mismatch: {original_files[rel_path]} vs {new_files[rel_path]}")
    print("Comparison complete")

# delete previous results, using shutil
shutil.rmtree('results', ignore_errors=True)

s = time()
samples = os.listdir('samples')
samples = [os.path.join('samples', sample) for sample in samples]
for sample in samples:
    parse_sgml_submission(filepath=sample, output_dir='results')

print(f"Time taken: {time() - s}")

compare_folders('results_comparison', 'results')