from argparse import ArgumentParser
import os
from datetime import datetime
import json
import subprocess
from config import load_json_file
from azure.storage.blob import BlobServiceClient
from config import load_env_vars
from LS_export_data_manually import get_tasks_export


def get_individual_tasks(debug=True):
    """
    Get all tasks from Label Studio.
    """
    task_data_dict = {}
    labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")
    for task_id in range(1,10000):
        task_json_name = f"task_data_{task_id}.json"
        if task_json_name in os.listdir():
            os.remove(task_json_name)
        sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json'  -X GET 'http://localhost:8080/api/tasks/{task_id}/' -o {task_json_name}", shell=True)

        # Load the task data
        task_data = load_json_file(task_json_name)

        # Stop whenever we reach the last task.
        # > the json will have a "status_code" key and a value of 404.
        if "status_code" in task_data and task_data["status_code"] == 404:
            break

        # If we have a task, add the task to the dict.
        task_data_dict[task_json_name] = task_data
    
    print(f">>> DEBUG <<< Get individual tasks, successfully.")

    return task_data_dict


def get_new_tasks_and_remove_duplicates(azure_storage_id=1, debug=True):
    """
    Get new tasks & remove duplicates.

    Args:
        debug (bool): Flag to print debug info.

    Returns:
        List(str): List of filtered task id(s).
    """

    try:
        labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")

        # Sync Import Storage. Load new images.
        sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/storages/azure/{azure_storage_id}/sync' -o sync_import_blob_imgs.json", shell=True)
        sync_import_blob_dict = load_json_file('sync_import_blob_imgs.json')
        if debug:
            print(f">>> DEBUG <<< Successfully synced import storage: {azure_storage_id}")
 
        # Get all tasks.
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_tasks_json_name = f"export_tasks_and_annotations_{current_time}.json"
        task_export_list = get_tasks_export(export_tasks_json_name, debug=debug)
        #task_data_dict = get_individual_tasks(debug=debug)
        # Create a set to store the task names.
        task_img_set = set()
        latest_task_i = 0
        task_id = 0

        # Iterate over the tasks and overwrite duplicates.
        good_tasks = []
        for task_dict in task_export_list:
        #for task_json_name, task_dict in task_data_dict.items():
            # Get the task metadeta for update.
            task_id = task_dict['id']
            task_data = task_dict['data']
            task_img = task_data['image']
            task_img_png = task_img.split("?")[0]
            task_project_id = task_dict['project']
            
            # Check if the task name is already in the set. If so, skip for now.
            if task_img_png in task_img_set:
                if debug:
                    # Print the task info.
                    print(f">>> DEBUG <<< SKIPPING DUPLICATE TASK: Task ID: {task_id}, Task Project: {task_project_id}, Task Data: {task_data}.")
                
                continue
            
            # If there is a gap, overwrite the next consecutive task_id with current data.
            if latest_task_i+1 < task_id:
                if debug:
                    # Print the task info.
                    print(f">>> DEBUG <<< PREPARE UPDATE: Old Task ID: {task_id}, New Task ID: {latest_task_i+1}, Task Project: {task_project_id}, Task Data: {task_data}.")
                
                task_id = latest_task_i+1
                good_tasks += [{"data": task_data, "meta": {}, "annotations": [], "predictions": []}]

                #task_update_dict = {"data": task_data, "project": task_project_id}
                #task_update_json_str = json.dumps(task_update_dict)
                #task_update_json_name = f"task_update_{task_id}.json"
                #if task_update_json_name in os.listdir():
                #    os.remove(task_update_json_name)
                #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X PATCH 'http://localhost:8080/api/tasks/{task_id}/' -d '{task_update_json_str}' -o {task_update_json_name}", shell=True)
                
            else:
                # Update task_id only until last item is found.
                latest_task_i += 1
            
            # Add the task name to the set.
            task_img_set.add(task_img_png)

        # Delete unneeded tasks.
        for i in range(latest_task_i, len(task_export_list)):
        #for task_id in range(latest_task_id+1, len(task_data_dict)+1):
            task_id = task_export_list[i]['id']
            if debug:
                # Print the task info.
                print(f">>> DEBUG <<< PREPARE DELETION Task ID: {task_id}")

            task_del_json_name = f"task_deletion_{task_id}.json"
            sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -X DELETE 'http://localhost:8080/api/tasks/{task_id}/'", shell=True)

            if debug:
                # Print the task info.
                print(f">>> DEBUG <<< DELETED Task ID: {task_id}")
        
        # Manually import good tasks.
        task_import_json_str = json.dumps(good_tasks)
        task_import_json_name = f"task_import_{task_id}.json"
        if task_import_json_name in os.listdir():
            os.remove(task_import_json_name)
        sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -H 'Content-Type: application/json' -X POST 'http://localhost:8080/api/projects/{task_project_id}/import' --data '{task_import_json_str}' -o {task_import_json_name}", shell=True)
        
        return [task_id for task_id in range(1, latest_task_i+len(good_tasks)+1)]
    
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
    get_new_tasks_and_remove_duplicates()
