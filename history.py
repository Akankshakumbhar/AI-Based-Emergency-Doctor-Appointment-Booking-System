import json
import os

def append_to_history(new_record, filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    data.append(new_record)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
