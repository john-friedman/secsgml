# SEC SGML

A python library to parse Securities and Exchange Commission [Standardized Generalized Markup Language](https://en.wikipedia.org/wiki/Standard_Generalized_Markup_Language). Used to power the open-source [datamule](https://github.com/john-friedman/datamule-python) project.

Currently parses two types of files:
1. [Daily Archives](https://www.sec.gov/Archives/edgar/Feed/)
2. [Submissions](https://www.sec.gov/Archives/edgar/data/1318605/000095017022000796/0000950170-22-000796.txt)

Will be expanded to also parse SGML Tables. 

[All Variations](submission_variations.md)

secsgml also attempts to standardize the metadata between formats. e.g. 'CENTRAL INDEX KEY' will be mapped to 'cik'.

## Installation
```
pip install secsgml
```
## Quickstart

### Parse into memory
```
from secsgml import parse_sgml_content_into_memory

# Takes either bytes_content or filepath
parse_sgml_content_into_memory(bytes_content=None, filepath=None)
```

### Write to tar
```
from secsgml import write_sgml_file_to_tar

# Takes either bytes_content or input_path
write_sgml_file_to_tar(output_path, bytes_content, input_path)
```

## Benchmarks
Using [500mb of SGML files](https://www.sec.gov/Archives/edgar/Feed/2009/QTR1/20090108.nc.tar.gz)
* write_sgml_file_to_tar - 3,960 ms
* parse_sgml_content_into_memory - 1,940 ms

pre v0.2.0 benchmark
* parse_sgml_content_into_memory (equivalent) - 5,750 ms