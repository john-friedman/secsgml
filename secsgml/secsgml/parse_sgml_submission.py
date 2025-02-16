from .sgml_memory_cy import parse_sgml_submission_into_memory
import os
import json

def parse_sgml_submission(content=None, filepath=None, output_dir=None):
    if not filepath and not content:
        raise ValueError("Either filepath or content must be provided")
    
    if not output_dir:
        os.makedirs(output_dir, exist_ok=True)

    header_metadata, documents = parse_sgml_submission_into_memory(filepath=filepath, content=content)
    try:
        accn = header_metadata['accession-number']
    except:
        accn = header_metadata['accession number']

    os.makedirs(f'{output_dir}/{accn}', exist_ok=True)

    with open(f'{output_dir}/{accn}/metadata.json', 'w') as f:
        json.dump(header_metadata, f, indent=4)

    for idx,_ in enumerate(header_metadata['documents']):
        try:
            filename = header_metadata['documents'][idx]['filename']
        except:
            filename = header_metadata['documents'][idx]['sequence'] + '.txt'
        with open(f'{output_dir}/{accn}/{filename}', 'wb') as f:
            f.write(documents[idx])