cpdef list extract_documents_fast(bytes data):
    cdef:
        char* ptr = data
        Py_ssize_t size = len(data)
        Py_ssize_t pos = 0, start_pos, end_pos
        list docs = []
    
    while pos < size:
        start_pos = data.find(b'<DOCUMENT>', pos)
        if start_pos == -1: break
        end_pos = data.find(b'</DOCUMENT>', start_pos + 10)
        if end_pos == -1: break
        docs.append(data[start_pos + 10:end_pos])
        pos = end_pos + 11
    
    return docs
