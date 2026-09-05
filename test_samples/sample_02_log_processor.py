def process_logs(log_file_path):
    try:
        log_file = open(log_file_path, 'r')
        error_count = 0
        
        for line in log_file:
            if 'ERROR' in line:
                error_count += 1
                print(f"Found error: {line.strip()}")
        
        return error_count
    finally:
        log_file.close()

def analyze_multiple_logs(file_paths):
    total_errors = 0
    
    for path in file_paths:
        with open(path, 'r') as f:
            content = f.read()
            total_errors += content.count('ERROR')
    
    return total_errors

if __name__ == "__main__":
    errors = process_logs("/var/log/app.log")
    print(f"Total errors: {errors}")
