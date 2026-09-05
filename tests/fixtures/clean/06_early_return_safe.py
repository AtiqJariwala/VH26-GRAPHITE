"""Safe handling of early return with try/finally."""

def process_file(filename):
    f = open(filename, "r")
    try:
        data = f.read()
        if not data:
            return None  # Safe: finally ensures close
        return data
    finally:
        f.close()
