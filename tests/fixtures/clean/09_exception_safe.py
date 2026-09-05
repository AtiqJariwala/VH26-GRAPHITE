"""Safe handling of exceptions with context manager."""

def parse_and_process(filename):
    with open(filename, "r") as f:
        import json
        # Even if json.loads raises, context manager closes the file
        data = json.loads(f.read())
        return process(data)

def process(data):
    return data
