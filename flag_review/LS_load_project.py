from argparse import ArgumentParser
import os
from datetime import datetime
import json
import subprocess
from config import load_json_file
from azure.storage.blob import BlobServiceClient
from config import load_env_vars
from LS_export_data_manually import get_tasks_export
from LS_load_json_files import load_labelstudio_json_to_str


def load_labelstudio_project(debug=True):
    """
    Create the project, connect to Azure, import tasks, and retrieve latest images.
    """
    labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")

    # Create New Project
    json_filename = "LS_jsons/create_new_project.json"
    out_json_filename = f"{json_filename[:-5]}_response.json"
    json_str = load_labelstudio_json_to_str(json_filename, debug)
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/projects' -d '{json_str}' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/projects' -d @LS_jsons/create_new_project.json -o new_project_response.json", shell=True)
    if debug:
        new_proj_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", new_proj_dict)
    
    # Create New Azure Import Storage
    json_filename = "LS_jsons/create_new_import_azure_blob_tasks.json"
    out_json_filename = f"{json_filename[:-5]}_response.json"
    json_str = load_labelstudio_json_to_str(json_filename, debug)
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/azure' -d '{json_str}' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/azure' -d @LS_jsons/create_new_import_azure_blob_tasks.json -o import_blob_tasks_setup_response.json", shell=True)
    if debug:
        import_blob_setup_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", import_blob_setup_dict)

    # Sync Import Storage
    out_json_filename = f"LS_jsons/sync_import_blob_response.json"
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/azure/1/sync' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/azure/1/sync' -o sync_import_blob_json.json", shell=True)
    if debug:
        sync_import_blob_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", sync_import_blob_dict)

    # Create New Azure Export Storge
    json_filename = "LS_jsons/create_new_export_azure_blob.json"
    out_json_filename = f"{json_filename[:-5]}_response.json"
    json_str = load_labelstudio_json_to_str(json_filename, debug)
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/export/azure' -d '{json_str}' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/export/azure' -d @LS_jsons/create_new_export_azure_blob.json -o export_blob_setup_response.json", shell=True)
    if debug:
        export_blob_setup_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", export_blob_setup_dict)
    # Sync Export Storage
    out_json_filename = f"LS_jsons/sync_export_blob_response.json"
    json_str = load_labelstudio_json_to_str(json_filename, debug)
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/export/azure/2/sync' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/export/azure/2/sync' -o sync_export_blob.json", shell=True)
    if debug:
        sync_export_blob_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", sync_export_blob_dict)

    # Update Import Storage for New Flags
    json_filename = "LS_jsons/create_new_import_azure_blob.json"
    out_json_filename = f"{json_filename[:-5]}_PATCH_response.json"
    json_str = load_labelstudio_json_to_str(json_filename, debug)
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X PATCH 'http://localhost:8080/api/storages/azure/1' -d '{json_str}' -o {out_json_filename}", shell=True)
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X PATCH 'http://localhost:8080/api/storages/azure/1' -d @LS_jsons/create_new_import_azure_blob.json -o import_blob_imgs_setup_response.json", shell=True)
    if debug:
        update_import_storage_dict = load_json_file(out_json_filename)
        print(f"******** DEBUG, {out_json_filename} ********", update_import_storage_dict)   


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug",
                        dest="debug", default=True,
                        help="Debug flag")
    
    pass
