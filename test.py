from secsgml import parse_sgml_submission_into_memory

metadata, docs = parse_sgml_submission_into_memory(filepath='samples/0001193805-23-001296.txt')
import json

with open('metadata.json', 'w') as f:
    json.dump(metadata, f, indent=4)