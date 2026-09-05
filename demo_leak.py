"""
Demo file showing a resource leak for judge presentation.
This is deliberately buggy to demonstrate LeakGuard's detection.
"""

def process_file(filename):
    """Process a file and return its contents.
    
    BUG: This function has a resource leak!
    The file is never closed if validation fails.
    """
    f = open(filename, 'r')
    
    # Validate the filename
    if not filename.endswith('.txt'):
        return None  # Early return - file never closed!
    
    # Read and process data
    data = f.read()
    f.close()
    
    return data.upper()


if __name__ == "__main__":
    result = process_file("data.txt")
    print(result)
