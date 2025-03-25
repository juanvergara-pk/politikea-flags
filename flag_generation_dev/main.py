import os
import sys
import json
import datetime
import cv2
import numpy as np
from argparse import ArgumentParser
from azure.storage.blob import BlobServiceClient

# LOAD MODULES FROM FLAG REVIEW "../flag_review/LS_export_data_manually.py".
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
flag_review_dir = os.path.abspath(os.path.join(parent_dir, 'flag_review'))
if flag_review_dir not in sys.path:
    #sys.path.insert(0, flag_review_dir)
    sys.path.insert(1, flag_review_dir)
from LS_export_data_manually import get_tasks_export_from_azure, TASK_NAME_F
# LOAD MODULES FROM FLAG FUNCTION APP "../flag-function-app/flag_generation/border_detection.py".
flag_function_app_dir = os.path.abspath(os.path.join(parent_dir, 'flag-function-app'))
if flag_function_app_dir not in sys.path:
    sys.path.insert(1, flag_function_app_dir)
from flag_generation.border_detection import detect_borders

## DOES NOT WORK:
## from ..flag_review.LS_export_data_manually import get_tasks_export_from_azure, TASK_NAME_F
## importlib.import_module("../flag_review/LS_export_data_manually.py")
# Load module from "../flag-function-app/flag_generation/border_detection.py".


def load_imgs_from_azure(export_tasks_data, debug=False):
    """
    Load imgs from Azure and manual annotations.

    Args:
        export_tasks_data (list): List of tasks data from labelstudio.
        debug (bool): Flag to print debug info.

    Returns:
        (dict, dict): Tuple of two dictionaries with loaded images and annotations, separately.
        -- img_dict (dict): Dictionary of cv2 loaded images.
        -- annotations_dict (dict): Dictionary of annotations.
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
        
        # Load the images from Azure.
        img_dict = {}
        annotations_dict = {}
        n_imgs = len(export_tasks_data)
        for i,task_data in enumerate(export_tasks_data):
            # Load img data.
            img_url = task_data["data"]["image"]
            img_name = img_url.split("/")[-1]
            # Skip if no annotations.
            if len(task_data["annotations"]) == 0:
                print(f"NOTE: Task {task_data['id']} has no annotations. We skip adding the image and the annotation.")
                continue
            img_annotation = task_data["annotations"][0]["result"][0]["value"]["choices"][0]
            # Skip if unnappealing flag.
            if img_annotation == "Unappealing flag":
                print(f"NOTE: Task {task_data['id']} was considered 'Unappealing flag'. We skip adding the image and the annotation.")
                continue
            # Record the annotation as a True/False statement as in border detection algorithm.
            img_annotation = img_annotation == "Has borders" #"Good flag"
            # Get the blob client for the image.
            img_blob_client = flag_container_client.get_blob_client(blob=img_name)

            # Download the image.
            #image_data = requests.get(image_url).content
            image_data = img_blob_client.download_blob().readall()
            #image = np.asarray(bytearray(image_data.read()), dtype="uint8")
            image = np.asarray(bytearray(image_data), dtype="uint8")
            #image = np.frombuffer(image_data, dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            # Store the image in the dictionary.
            img_dict[img_name] = image
            annotations_dict[img_name] = img_annotation

            if debug:
                print(f"Loaded image {(i+1):4}/{n_imgs:4}: '{img_name}' with border annotation: '{img_annotation}'.")
        
        if debug:
            print(f"Successfully loaded {len(img_dict)} images and {len(annotations_dict)} annotations.")

        return img_dict, annotations_dict
    
    except Exception as e:
        raise RuntimeError(f"Failed happen while loading Azure images: {str(e)}")
    

def get_border_detection_predictions(img_dict, detect_borders_algo=detect_borders, debug=False):
    """
    Run the border detection algorithm on the images.

    Args:
        img_dict (dict): Dictionary of cv2 loaded images.
        detect_borders_algo (function): Algorithm to detect borders.
            By default, it uses the detect_borders function from 'flag-function-app'.
        debug (bool): Flag to print debug info.

    Returns:
        (dict, dict): Tuple of two dictionaries with loaded predictions and processed imgs with
                      detected borders, separately.
        -- predictions_dict (dict): Dictionary of annotations.
        -- img_w_borders_dict (dict): Dictionary of imgs with flagged borders.

    """
    
    # Iterate over the images.
    predictions_dict = {}
    img_w_borders_dict = {}
    for img_name, image in img_dict.items():

        # Detect borders.
        img_has_borders, borders_sum, out_img = detect_borders_algo(image)
        if debug:
            print(f"Image: {img_name} has borders: {img_has_borders}, sum: {borders_sum}")
        
        # Store the prediction.
        predictions_dict[img_name] = img_has_borders
        img_w_borders_dict[img_name] = out_img
    
    return predictions_dict, img_w_borders_dict


def compare_predictions_against_labels(annotations_dict, predictions_dict, debug=False):
    """
    Score the performance of the algorithm.

    Args:
        annotations_dict
        predictions_dict
        debug (bool): Flag to print debug info.

    Returns:
        List(str): List of found task id(s).
    """

    # Compare the predictions against the labels.
    mismatched_tasks = []
    total_images = len(annotations_dict)
    correct_predictions = 0

    for img_name, annotation in annotations_dict.items():
        prediction = predictions_dict.get(img_name, None)
        if prediction is None:
            if debug:
                print(f"Image {img_name} is missing in predictions.")
            continue

        if annotation == prediction:
            correct_predictions += 1
        else:
            mismatched_tasks.append(img_name)
            if debug:
                print(f"Mismatch for image {img_name}: Annotation={annotation}, Prediction={prediction}")

    accuracy = correct_predictions / total_images if total_images > 0 else 0
    if debug:
        print(f"Accuracy: {(accuracy*100):.1f}% ({correct_predictions}/{total_images})")

    return mismatched_tasks, accuracy
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-efn", "--export_fn",
                        dest="export_fn", default="export_tasks_and_annotations.json",
                        help="Filename of the export tasks and annotations in Azure.")
    parser.add_argument("-d", "--debug",
                        dest="debug", default=False,
                        help="Debug flag")

    args = parser.parse_args()
    export_fn = args.export_fn
    debug = args.debug

    from config import load_env_vars
    load_env_vars()

    # Get the tasks export from Azure.
    export_fn = "export_tasks_and_annotations_20250318_122733.json"
    export_tasks_data = get_tasks_export_from_azure(azure_export_fn=export_fn, debug=debug)

    # Load the images from Azure.
    img_dict, annotations_dict = load_imgs_from_azure(export_tasks_data, debug=True) #debug)

    # Run the border detection algorithm on the images.
    predictions_dict, img_w_borders_dict = get_border_detection_predictions(img_dict, debug=debug)

    # Compare the predictions against the labels.
    mismatched_tasks, accuracy = compare_predictions_against_labels(annotations_dict, predictions_dict, debug=debug)
