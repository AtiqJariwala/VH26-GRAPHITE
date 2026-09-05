"""File leak due to early return before close()."""

def process_file(filename):
    f = open(filename, "r")
    
    data = f.read()
    
    if not data:
        return None  # LEAK: early return without closing
    
    f.close()
    return data
