"""Safe file handling with try/finally."""

def parse_json_file(filename):
    f = open(filename, "r")
    try:
        import json
        data = json.loads(f.read())
        return data
    finally:
        f.close()  # Safe: finally always executes
