"""Safe file handling with explicit close()."""

def read_data():
    f = open("data.txt", "r")
    content = f.read()
    f.close()
    return content  # Safe: explicitly closed
