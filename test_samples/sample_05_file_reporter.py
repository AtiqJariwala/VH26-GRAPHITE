import threading

def generate_report(input_file, output_file):
    # Read input
    with open(input_file, 'r') as infile:
        data = infile.readlines()
    
    # Process data
    processed = [line.upper() for line in data]
    
    # Write output
    with open(output_file, 'w') as outfile:
        outfile.writelines(processed)

def parallel_report_generation(file_pairs):
    lock = threading.Lock()
    threads = []
    
    for input_file, output_file in file_pairs:
        def worker():
            lock.acquire()
            generate_report(input_file, output_file)
            lock.release()
        
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

def quick_summary(file_path):
    f = open(file_path, 'r')
    lines = f.readlines()
    f.close()
    
    return {
        'line_count': len(lines),
        'char_count': sum(len(line) for line in lines),
        'first_line': lines[0] if lines else ''
    }

if __name__ == "__main__":
    summary = quick_summary("data.txt")
    print(f"Summary: {summary}")
