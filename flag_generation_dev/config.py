import os
import json

def load_json_file(json_fn):
    json_dict = {}
    with open(json_fn, 'r') as f:
        json_dict = json.load(f)
    return json_dict

def load_env_vars(config=None):
    if not config:
        config = load_json_file('config.json')
    ## Load OpenAI API Key and Endpoint
    os.environ["AZURE_OPENAI_API_KEY"]=config['AZURE_OPENAI_API_KEY']
    os.environ["AZURE_OPENAI_ENDPOINT"]=config['AZURE_OPENAI_ENDPOINT']
    # Blob Storage Connection String
    os.environ["AZURE_STORAGE_CONNECTION_STRING"] = config["AZURE_STORAGE_CONNECTION_STRING"]
    os.environ["AZURE_STORAGE_ACCOUNT"] = config['AZURE_STORAGE_ACCOUNT']
    os.environ["AZURE_STORAGE_KEY"] = config['AZURE_STORAGE_KEY']
    os.environ["CONTAINER_NAME"] = config['CONTAINER_NAME']
    os.environ["LABELSTUDIO_SUBFOLDER"] = config['LABELSTUDIO_SUBFOLDER']
    os.environ["LABELSTUDIO_TOKEN"] = config['LABELSTUDIO_TOKEN']
