# This file has NO resource leaks - all resources are properly managed

def process_data_safe():
    """Safely processes data using context manager"""
    with open('data.txt') as f:
        if not validate_data(f):
            return None  # Safe: context manager closes file automatically
        return parse(f)

def process_multiple_files():
    """Handles multiple files safely"""
    with open('input.txt') as input_file:
        data = input_file.read()

    with open('output.txt', 'w') as output_file:
        output_file.write(data.upper())

    return True

def explicit_close_example():
    """Demonstrates explicit close (but context manager is better)"""
    f = open('config.txt')
    try:
        config = f.read()
        return config
    finally:
        f.close()  # Always closes, even if exception occurs

def validate_data(file):
    """Helper function"""
    return len(file.read()) > 0

def parse(file):
    """Helper function"""
    return file.read()

# All resources in this file are properly closed!
# LeakGuard will report: "No resource leaks detected" ✅
