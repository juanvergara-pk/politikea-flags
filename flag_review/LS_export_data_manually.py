from argparse import ArgumentParser
import os
from datetime import datetime
import json
import subprocess
from azure.storage.blob import BlobServiceClient
from config import load_json_file, load_env_vars

# Name tasks using Task ID and setting 4 leading zeroes.
TASK_NAME_F = lambda task_id: f"task_data_v2_{task_id:05}.json"


def get_tasks_export(export_tasks_json_name = "export_tasks_and_annotations.json", debug=True):
    """
    Get a full project export with projects and annotations.
    Tasks need to be later split into individual json files.
    """
    # Prepare the ls token & export file name.
    labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")
    
    # Remove previous export file if it exists.
    if export_tasks_json_name in os.listdir():
        os.remove(export_tasks_json_name)
    
    # Run the curl command to get the export.
    sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Accept: application/json'  -X GET 'http://localhost:8080/api/projects/{1}/export?exportType=JSON&download_all_tasks=true' -o '{export_tasks_json_name}'", shell=True)
    export_tasks_dict = load_json_file(export_tasks_json_name)

    return export_tasks_dict


def get_individual_tasks(debug=True):
    """
    (unused) Import format is different. Use 'get_tasks_export' instead.
    Export all tasks from Label Studio.
    """
    task_data_dict = {}
    labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")
    for task_id in range(1,10000):
        task_json_name = f"task_data_{task_id}.json"
        if task_json_name in os.listdir():
            os.remove(task_json_name)
        sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Accept: application/json'  -X GET 'http://localhost:8080/api/tasks/{task_id}/' -o {task_json_name}", shell=True)

        # Load the task data
        task_data = load_json_file(task_json_name)

        # Stop whenever we reach the last task.
        # > the json will have a "status_code" key and a value of 404.
        if "status_code" in task_data and task_data["status_code"] == 404:
            break

        # If we have a task, add the task to the dict.
        task_data_dict[task_json_name] = task_data
    
    return task_data_dict


def get_tasks_export_from_azure(azure_export_fn="export_tasks_and_annotations.json", debug=True):

    try:
        blob_url = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        container_name = os.getenv("CONTAINER_NAME")
        labelstudio_folder = os.getenv("LABELSTUDIO_SUBFOLDER")

        # Construct the correct container and label subfolder URLs
        container_blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}"
        label_blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{labelstudio_folder}"

        # Create a blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_url)
        # Create a blob client for the flag container.
        flag_container_client = blob_service_client.get_container_client(container_name)
        # Create a blob client for the labelstudio subfolder.
        #label_folder_client = flag_container_client.get_container_client(container=label_studio_folder)
        #label_folder_client = blob_service_client.get_container_client(container=container_name+"/"+label_studio_folder)
        # Use the prefix to target the "label_studio_folder" and "subfolder"
        labelstudio_prefix = f"{labelstudio_folder}/"  # Ensure it ends with '/'

        # Get the export from azure. Load the exported file.
        export_tasks_blob_client = flag_container_client.get_blob_client(blob=azure_export_fn)
        ls_label_data = export_tasks_blob_client.download_blob().readall()
        export_tasks_data = json.loads(ls_label_data)

        if debug:
            print(f"EXPORTED TASKS:\n{len(export_tasks_data)}")
        
        return export_tasks_data

    except Exception as e:
        raise RuntimeError(f"Failed happen during loading labels step: {str(e)}")


def export_tasks_and_annotations(debug=True):
    """
    Export tasks & annotations from Label Studio.
    This step is required so tasks are loaded correctly into Label Studio.

    Args:
        debug (bool): Flag to print debug info.

    Returns:
        List(str): List of found task id(s).
    """

    try:
        blob_url = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        container_name = os.getenv("CONTAINER_NAME")
        labelstudio_folder = os.getenv("LABELSTUDIO_SUBFOLDER")

        # Construct the correct container and label subfolder URLs
        container_blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}"
        label_blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{labelstudio_folder}"

        # Create a blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_url)
        # Create a blob client for the flag container.
        flag_container_client = blob_service_client.get_container_client(container_name)
        
        ## Use the prefix to target the "label_studio_folder" and "subfolder"
        #labelstudio_prefix = f"{labelstudio_folder}/"  # Ensure it ends with '/'
        ## List Blob Names, and iterate over them.
        #labelstudio_labels = flag_container_client.list_blobs(name_starts_with=labelstudio_prefix)
        #for ls_label_blob in labelstudio_labels:
        #    if debug:
        #        print(f"Processing LabelStudio Config: {ls_label_blob['name']}.")
        #    # Get the Blob Client.
        #    ls_label_client = flag_container_client.get_blob_client(blob=ls_label_blob.name)
        #
        #    # Prepare the label name.
        #    ls_label_name = ls_label_client.blob_name.split("/")[-1]
        #    # Continue if it is already a json file.
        #    if ls_label_name.endswith(".json"):
        #        continue
        #    # If not, add json and recreate.
        #    ls_label_name = ls_label_name + ".json"
        #
        #    # Download the blob data.
        #    ls_label_data = ls_label_client.download_blob().readall()
        #
        #    # Recreate label
        #    #new_label_dict = setup_new_label(ls_label_data)
        #
        #    # Create duplicate in parent folder.
        #    ls_label_blob_client_2 = flag_container_client.get_blob_client(blob=ls_label_name)
        #    ls_label_blob_client_2.upload_blob(ls_label_data, overwrite=True)
        #    #if not latest_date or blob.last_modified > latest_date:
        #    #    latest_label = blob
        #    #    latest_date = blob.last_modified

        ## Get all tasks.
        #task_data_dict = get_all_tasks(debug=debug)
        ## Save all tasks to storage.
        #for task_json_name, task_data in task_data_dict.items():
        #    if debug:
        #        print(f"Processing: {task_json_name}.")
        #    
        #    task_json_str = json.dumps(task_data, indent=4)
        #    task_blob_client = flag_container_client.get_blob_client(blob=task_json_name)
        #    task_blob_client.upload_blob(task_json_str, overwrite=True)

        # Export all tasks.
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_tasks_json_name = f"export_tasks_and_annotations_{current_time}.json"
        export_tasks_data = get_tasks_export(export_tasks_json_name, debug=debug)
        for task_data in export_tasks_data:
            task_json_name = TASK_NAME_F(task_data['id'])
            # Prepare the task data.
            task_json_str = json.dumps(task_data, indent=4)
            # Store the task data in the blob.
            task_blob_client = flag_container_client.get_blob_client(blob=task_json_name)
            task_blob_client.upload_blob(task_json_str, overwrite=True)
        # Store the export tasks in a single blob too.
        export_tasks_str = json.dumps(export_tasks_data, indent=4)
        export_tasks_blob_client = flag_container_client.get_blob_client(blob=export_tasks_json_name)
        export_tasks_blob_client.upload_blob(export_tasks_str, overwrite=True)

        # TODO: AUX TEST. Save project.json with main labels
        #from config import load_json_file
        #label_name_aggregated = "project-1-at-2025-02-20-18-58-bc7ff687.json"
        #project_dict = load_json_file(f".aux/{label_name_aggregated}")
        #project_json = json.dumps(project_dict, indent=4)
        #ls_label_blob_client_2 = flag_container_client.get_blob_client(blob=label_name_aggregated)
        #ls_label_blob_client_2.upload_blob(project_json, overwrite=True)

        return [task_data['id'] for task_data in export_tasks_data]
    
    except Exception as e:
        raise RuntimeError(f"Failed happen during loading labels step: {str(e)}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-e", "--export",
                        dest="export", default=True,
                        help="Run Export of Tasks and Annotations")
    
    # Load env vars.
    load_env_vars()

    # Recreate labels.
    export_tasks_and_annotations()
