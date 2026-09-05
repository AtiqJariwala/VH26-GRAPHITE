"""Resource passed to unknown function - ownership unclear."""

def process_with_helper(filename):
    f = open(filename, "r")
    # We don't know if process_data closes the file or not
    result = process_data(f)  # POSSIBLE LEAK: ownership unclear
    return result

def process_data(file_obj):
    # Does this close the file? We can't tell without inter-procedural analysis
    return file_obj.read()
