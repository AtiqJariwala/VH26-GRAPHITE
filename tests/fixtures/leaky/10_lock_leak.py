"""Threading lock acquired but never released."""

import threading

def critical_section():
    lock = threading.Lock()
    lock.acquire()
    # Do some work
    result = process_shared_data()
    if result is None:
        return None  # LEAK: lock not released on early return
    
    lock.release()
    return result

def process_shared_data():
    return "data"
