"""Leak on one branch of conditional."""

def read_config(use_json):
    f = open("config.txt", "r")
    
    if use_json:
        import json
        result = json.load(f)
        f.close()
        return result
    else:
        # Simple text reading
        result = f.read()
        return result  # LEAK: close() only in if-branch
