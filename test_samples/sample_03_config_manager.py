import json

def load_config(config_path):
    config_file = open(config_path, 'r')
    config_data = json.load(config_file)
    return config_data

def save_config(config_path, config_data):
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)

def update_config(config_path, key, value):
    config = load_config(config_path)
    config[key] = value
    save_config(config_path, config)
    return True

def validate_config(config_path):
    try:
        f = open(config_path, 'r')
        data = json.load(f)
        f.close()
        
        required_keys = ['host', 'port', 'database']
        for key in required_keys:
            if key not in data:
                return False
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

if __name__ == "__main__":
    update_config("config.json", "debug", True)
