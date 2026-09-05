"""Simple file leak - no close() called."""

def read_data():
    f = open("data.txt", "r")
    content = f.read()
    return content  # LEAK: file never closed
