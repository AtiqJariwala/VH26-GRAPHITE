"""Safe lock handling with context manager."""

import threading

def critical_section():
    lock = threading.Lock()  # Create lock (not yet acquired)
    with lock:  # Safe: context manager handles acquire/release
        result = process_shared_data()
        if result is None:
            return None
        return result

def process_shared_data():
    return "data"
