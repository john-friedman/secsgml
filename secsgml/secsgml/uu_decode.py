import binascii
import os
import sys
from io import BytesIO

class Error(Exception):
    pass

def decode(in_file, out_file=None, mode=None, quiet=False):
    """Decode uuencoded file"""
    opened_files = []
    
    # Pre-compile constant bytes objects
    BEGIN = b'begin'
    END = b'end'
    SPACE = b' '
    WHITESPACE = b' \t\r\n\f'
    
    # Handle input file
    if in_file == '-':
        in_file = sys.stdin.buffer
    elif isinstance(in_file, str):
        in_file = open(in_file, 'rb')
        opened_files.append(in_file)

    try:
        # Read file content into memory for faster processing
        content = in_file.readlines()
        
        # Find begin line
        for hdr in content:
            if hdr.startswith(BEGIN):
                hdrfields = hdr.split(SPACE, 2)
                if len(hdrfields) == 3 and hdrfields[0] == BEGIN:
                    try:
                        int(hdrfields[1], 8)
                        break
                    except ValueError:
                        continue
        else:
            raise Error('No valid begin line found in input file')

        # Handle output file
        if out_file is None:
            out_file = hdrfields[2].rstrip(WHITESPACE).decode("ascii")
            if os.path.exists(out_file):
                raise Error(f'Cannot overwrite existing file: {out_file}')
            if (out_file.startswith(os.sep) or
                f'..{os.sep}' in out_file or (
                    os.altsep and
                    (out_file.startswith(os.altsep) or
                     f'..{os.altsep}' in out_file))
               ):
                raise Error(f'Refusing to write to {out_file} due to directory traversal')

        if mode is None:
            mode = int(hdrfields[1], 8)

        # Handle output file opening
        if out_file == '-':
            out_file = sys.stdout.buffer
        elif isinstance(out_file, str):
            fp = open(out_file, 'wb')
            os.chmod(out_file, mode)
            out_file = fp
            opened_files.append(out_file)

        # Process content in bulk
        buffer = BytesIO()
        start_idx = content.index(hdr) + 1
        
        for line in content[start_idx:]:
            stripped = line.strip(WHITESPACE)
            if not stripped or stripped == END:
                break
                
            try:
                data = binascii.a2b_uu(line)
            except binascii.Error as v:
                # Workaround for broken uuencoders
                nbytes = (((line[0]-32) & 63) * 4 + 5) // 3
                data = binascii.a2b_uu(line[:nbytes])
                if not quiet:
                    sys.stderr.write("Warning: %s\n" % v)
            
            buffer.write(data)
        
        # Write all data at once
        out_file.write(buffer.getvalue())
        
    finally:
        for f in opened_files:
            f.close()