"""File leak on exception path - close() only on happy path."""

def parse_json_file(filename):
    f = open(filename, "r")
    
    # If this raises an exception, file is never closed
    import json
    data = json.loads(f.read())  # LEAK: exception skips close()
    
    f.close()
    return data
