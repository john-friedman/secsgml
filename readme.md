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
from secsgml import parse_sgml_submission_into_memory
metadata,documents = parse_sgml_submission_into_memory(filepath="000000443897000001.sgml")
```

### Parse to file
```
from secsgml import parse_sgml_submission
# from file
parse_sgml_submission(filepath='samples/0000891618-94-000021.txt',output_dir='results')

# from content
parse_sgml_submission(content=sgml_content,output_dir='results')
```

## Note
Will be giving parse_sgml_submission_into_memory more love, will have to refactor parse_sgml_submission afterwards. 

## Future
* SGML Table parsing
* Optimization + refactor in Cython/ C bindings.
