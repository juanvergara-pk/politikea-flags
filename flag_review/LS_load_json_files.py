from argparse import ArgumentParser
import os
from datetime import datetime
import json
import subprocess
from config import load_json_file
from azure.storage.blob import BlobServiceClient
from config import load_env_vars
from LS_export_data_manually import get_tasks_export


def load_labelstudio_json_to_str(json_file, debug=True):
    """
    Load the labelstudio files & add secrets from env vars.
    Return the output in string format
    
    Args:
        json_file (str): The json file to load.
        debug (bool): Debug flag.

    Returns:
        str: The json data in string format.
    """
    
    # Load json file
    json_data = load_labelstudio_json(json_file, debug)
    if debug:
        print("******** DEBUG ********", json_data)
    
    # Convert json data to string
    json_str = json.dumps(json_data)

    return json_str


def load_labelstudio_json(json_file, debug=True):
    """
    Load the labelstudio files & add secrets from env vars.
    
    Args:
        json_file (str): The json file to load.
        debug (bool): Debug flag.

    Returns:
        dict: The loaded json data.
    """
    azure_storage_key = os.getenv("AZURE_STORAGE_KEY")
    container_name = os.getenv("CONTAINER_NAME")
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT")

    # Load json file
    json_data = load_json_file(json_file)
    if debug:
        print("******** DEBUG ********", json_data)
    
    # Load necessary keys if applicable.
    if "azure" in json_file:
        if "account_key" in json_data:
            json_data["account_key"] = azure_storage_key
        if "container" in json_data:
            json_data["container"] = container_name
        if "account_name" in json_data:
            json_data["account_name"] = account_name

    # Return the updated json data.
    return json_data


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug",
                        dest="debug", default=True,
                        help="Debug flag")
    
    pass
