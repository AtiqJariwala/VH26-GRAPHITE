"""Safe file handling with context manager."""

def read_data():
    with open("data.txt", "r") as f:
        content = f.read()
    return content  # Safe: context manager handles close
