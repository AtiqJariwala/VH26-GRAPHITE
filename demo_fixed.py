"""
Fixed version - no resource leak.
Context manager ensures file is always closed.
"""

def process_file(filename):
    """Process a file and return its contents - SAFE VERSION."""
    with open(filename, 'r') as f:
        # Validate the filename
        if not filename.endswith('.txt'):
            return None  # File automatically closed even on early return!
        
        # Read and process data
        data = f.read()
        return data.upper()


if __name__ == "__main__":
    result = process_file("data.txt")
    print(result)
