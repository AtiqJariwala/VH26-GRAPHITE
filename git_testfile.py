# This file has a resource leak
def process_data():
    f = open('data.txt')
    if not validate_data(f):
        return None  # BUG: file never closed!
    f.close()
    return parse(f)

def validate_data(file):
    return True

def parse(file):
    return file.read()
