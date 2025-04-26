import json
import os

CONFIG_FILE = 'user_config.json'

def get_config(key, default=None):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f).get(key, default)
    return default

def save_config(key, value):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    config[key] = value
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f) 