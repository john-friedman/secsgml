# File to implement metadata mapping after parsing SGML files

from .sgml_memory_cy import parse_sgml_submission_into_memory as parse_sgml_memory_cy
import re
sec_format_mappings = {
    "accession number": "accession-number",
    "conformed submission type": "type",
    "public document count": "public-document-count",
    "conformed period of report": "period",
    "filed as of date": "filing-date",
    "date as of change": "date-of-filing-date-change",
    
    # Filer section - company data
    "company data": "company-data",
    "company conformed name": "conformed-name",
    "central index key": "cik",
    "standard industrial classification": "assigned-sic",
    "irs number": "irs-number",
    "state of incorporation": "state-of-incorporation",
    "fiscal year end": "fiscal-year-end",
    
    # Filer section - filing values
    "filing values": "filing-values",
    "form type": "form-type",
    "sec act": "act",
    "sec file number": "file-number",
    "film number": "film-number",
    
    # Filer section - business address
    "business address": "business-address",
    "street 1": "street1",
    "city": "city",
    "state": "state",
    "zip": "zip",
    "business phone": "phone",
    
    # Filer section - mail address
    "mail address": "mail-address",
    
    # Filer section - former company
    "former company": "former-company",
    "former conformed name": "former-conformed-name",
    "date of name change": "date-changed",    
}

def transform_metadata(metadata):
    if not isinstance(metadata, dict):
        return metadata
    
    result = {}
    
    for key, value in metadata.items():
        if key == "documents":
            result[key] = value
            continue
        
        # Apply mapping if exists, otherwise remove dashes
        new_key = sec_format_mappings.get(key, key.replace(" ", "-"))
        
        # Special handling for SIC and Act fields
        if new_key == "assigned-sic" and isinstance(value, str):
            # Extract just the numeric portion from SIC like "MOTOR VEHICLES & PASSENGER CAR BODIES [3711]"
            sic_match = re.search(r'\[(\d+)\]', value)
            if sic_match:
                value = sic_match.group(1)
        elif new_key == "act" and isinstance(value, str) and "Act" in value:
            # Extract just the last two digits from "1934 Act"
            act_match = re.search(r'(\d{2})(\d{2})\s+Act', value)
            if act_match:
                value = act_match.group(2)
        
        # Recursively transform nested dictionaries
        if isinstance(value, dict):
            result[new_key] = transform_metadata(value)
        else:
            result[new_key] = value
    
    return result

def parse_sgml_submission_into_memory(content=None, filepath=None):
    metadata, documents = parse_sgml_memory_cy(content, filepath)
    
    transformed_metadata = transform_metadata(metadata)
    
    return transformed_metadata, documents

