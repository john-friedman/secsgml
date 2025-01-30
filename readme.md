# SEC SGML (Not ready for use yet)

A python library to parse Securities and Exchange Commission [Standardized Generalized Markup Language](https://en.wikipedia.org/wiki/Standard_Generalized_Markup_Language). Used to power the open-source [datamule](https://github.com/john-friedman/datamule-python) project.

Currently parses two types of files:
1. [Daily Archives](https://www.sec.gov/Archives/edgar/Feed/)
2. [Submissions](https://www.sec.gov/Archives/edgar/data/1318605/000095017022000796/0000950170-22-000796.txt)

Will be expanded to also parse SGML Tables. 

[All Variations](submission_variations.md)

## Installation
```
pip install secsgml
```
## Quickstart
```
parse_sgml_submission(filepath='samples/0000891618-94-000021.txt',output_dir='results')
```

## Future
* SGML Table parsing
* Optimization + refactor in Cython/ C bindings.



