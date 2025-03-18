import json

def load_json_file(json_fn):
    json_dict = {}
    with open(json_fn, 'r') as f:
        json_dict = json.load(f)
    return json_dict
