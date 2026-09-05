"""Safe handling with close on all branches."""

def read_config(use_json):
    f = open("config.txt", "r")
    
    if use_json:
        import json
        result = json.load(f)
        f.close()
        return result
    else:
        result = f.read()
        f.close()  # Safe: close on all branches
        return result
