"""Variable reassignment - original resource lost."""

def process_files():
    f = open("file1.txt", "r")
    data1 = f.read()
    
    # Reassigning without closing the first file
    f = open("file2.txt", "r")  # LEAK: original file handle lost
    data2 = f.read()
    f.close()
    
    return data1 + data2
