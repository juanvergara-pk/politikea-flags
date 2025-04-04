import os
import datetime
import re
import cv2
import json
import requests
import random
import numpy as np
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
try:
    from flag_generation.border_detection import detect_borders
except:
    from border_detection import detect_borders

def create_batch_flags(n_flags: int, elements: list[str], styles: list[str], colors: list[str], items: list[str], n_attempts: bool = 1) -> list:
    """
    Creates a batch of flags randomly using the given elements, styles, colors, and items.

    Args:
        n_flags (int): The number of flags to create.
        elements (list[str]): A list of natural elements to include in the flags.
        styles (list[str]): A list of primary image styles.
        colors (list[str]): A list of primary colors of the flags.
        items (list[str]): A list of additional animals or objects to be included.
        n_attempts (int): The number of attempts to generate an image
                          if borders are detected.

    Returns:
        list: A list of public URLs of the stored images in Azure Blob Storage.
    """
    try:
        batch_flags = []
        for i in range(n_flags):
            element = random.choice(elements)
            style = random.choice(styles)
            color = random.choice(colors)
            item = random.choice(items)
            flag_url = generate_flag_wout_borders(element, style, color, item, n_attempts)
            batch_flags.append(flag_url)
        return batch_flags

    except Exception as e:
        raise RuntimeError(f"Failed to generate batch of flags: {str(e)}")


def generate_flag_wout_borders(element: str, style: str, color: str, item: str, n_attempts: bool = 3) -> str:
    """
    Generates an OpenAI image for a flag, recreates it until no borders are detected,
    and stores it in Azure Blob Storage.

    Args:
        element (str): A natural element to include in the flag.
        style (str): The primary image style.
        color (str): The primary color of the flag.
        item (str): An additional animal or object to be included.
        n_attempts (int): The number of attempts to generate an image
                          if borders are detected.

    Returns:
        str: The public URL of the stored image in Azure Blob Storage.
    """
    try:
        for _ in range(n_attempts):
            stored_image_url, img_params = generate_and_store_flag(element, style, color, item)
            img_has_borders = img_params["has_borders"]
            if not img_has_borders:
                return stored_image_url
        return stored_image_url # TODO: Add img_params to function app if wanting to return more stuff.

    except Exception as e:
        raise RuntimeError(f"Failed to batch img generation & storage: {str(e)}")


def generate_and_store_flag(element: str, style: str, color: str, item: str, save_metadata: bool = False) -> str:
    """
    Generates an OpenAI image for a flag and stores it in Azure Blob Storage.

    Args:
        element (str): A natural element to include in the flag.
        style (str): The primary image style.
        color (str): The primary color of the flag.
        item (str): An additional animal or object to be included.

    Returns:
        str: The public URL of the stored image in Azure Blob Storage.
    """
    try:
        # Create image.
        image_url, og_prompt, rev_prompt = create_flag(element, style, color, item)
        # Download the image.
        image_data = requests.get(image_url).content
        image = np.asarray(bytearray(image_data), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # Detect borders.
        img_has_borders, borders_sum, out_img = detect_borders(image)
        # Store img in azure.
        img_params = {
            "original_prompt": og_prompt,
            "revised_prompt": rev_prompt,
            "has_borders": img_has_borders,
            "element": element,
            "style": style,
            "color": color,
            "item": item
        }
        stored_image_url, img_params = store_flag_image(image_data, img_params, save_metadata, img_has_borders)
        return stored_image_url, img_params

    except Exception as e:
        raise RuntimeError(f"Failed to generate and store image: {str(e)}")


def create_flag(element: str, style: str, color: str, item: str) -> str:
    """
    Calls OpenAI's DALL·E to generate an image and returns the image data (bytes).
    
    Args:
        prompt (str): The text prompt for image generation.
        element (str): A natural element to include in the flag.
        style (str): The primary image style.
        color (str): The primary color of the flag.
        item (str): An additional animal or object to be included.

    Returns:
        bytes: The raw image data.
    """
    try:

        # Build dynamic prompt
        #prompt = "I want a rectangular horizontal image. It must have a tribal style. The image must not be too cluttered. The image must be harmoniously balanced. The image must include: An elephant, The color orange tiger, and Grass"
        #prompt = (
        #    f"I want a rectangular horizontal image. "
        #    f"It must have a tribal style. The image must not be too cluttered. "
        #    f"The image must be harmoniously balanced. The image must include: "
        #    f"An {animal}, The color {color}, and {object}."
        #)
        prompt_f = lambda element, style, color, item: (
            f"I want a rectangular horizontal image. "
            f"It must have a {style} style. The image must not be too cluttered. "
            f"The image must be harmoniously balanced. The image must include: "
            f"- The color {color}; - A(n) {item}; - A(n) {element}."
        )
        # PROMPT REWRITING: https://platform.openai.com/docs/guides/images#dall-e-3-prompting
        base_prompt = "" #"I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"
        prompt = base_prompt + prompt_f(element, style, color, item)
        # WHAT's NEW WITH DALL-E-3: https://cookbook.openai.com/articles/what_is_new_with_dalle_3
        
        image_url, revised_prompt = call_openai_img_endpoint(prompt)

        return image_url, prompt, revised_prompt
    
    except Exception as e:
        raise RuntimeError(f"Failed to generate image: {str(e)}")


def store_flag_image(image_data, img_params, save_metadata=False, img_has_borders=False) -> str:#
    """
    Downloads an image from OpenAI and uploads it to Azure Blob Storage.

    Args:
        image_data (img_data): The generated image in raw bytes format, ready
                               for Azure Storage.
        img_params (dict): A dictionary containing the image parameters.
        save_metadata (bool): A flag to save the image metadata in Azure Blob Storage.
        img_has_borders (bool): A flag indicating if the image has borders.

    Returns:
        str: The public URL of the stored image in Azure Blob Storage.
    """

    try:
        blob_url = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        container_name = os.getenv("CONTAINER_NAME")
        account_key = os.getenv("AZURE_STORAGE_KEY")

        ## Download the image.
        #image_data = requests.get(image_url).content
        #image_name = "futuristic_city.png"
        image_name = create_img_name(img_params, img_has_borders)
        img_params["image_name"] = image_name

        # Create a blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_url)
        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=image_name)
        # Upload the created file
        blob_client.upload_blob(image_data, overwrite=True)

        if save_metadata:
            # Store image metadata (img_params) in json format. Includes the revised prompt.
            metadata = json.dumps(img_params)
            metadata_blob_name = image_name.replace(".png", ".json")
            metadata_blob_client = blob_service_client.get_blob_client(container=container_name, blob=metadata_blob_name)
            metadata_blob_client.upload_blob(metadata, overwrite=True)

        # Get a sharable link with a SAS token with read access.
        #blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{image_name}"
        blob_url = blob_client.url
        current_time = datetime.datetime.now(datetime.timezone.utc)
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=storage_account,
            container_name=container_name,
            blob_name=image_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            # 100 years PETICION JUAN CARDELUS Y JOSE MONTES. Que Dios nos coja confesados.
            expiry=current_time + datetime.timedelta(weeks=5600),
            start=current_time,
        )
        # Append SAS token to the blob URL.
        blob_url = blob_client.url + "?" + sas_token

        return blob_url, img_params
    
    except Exception as e:
        raise RuntimeError(f"Failed to store image: {str(e)}")


def create_img_name(img_params, img_has_borders=False) -> str:
    name = ""
    try:
        # Extract params.
        element = img_params["element"]
        style = img_params["style"]
        color = img_params["color"]
        item = img_params["item"]
        # Create preliminary ID.
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        name = f"{timestamp}_E_{element}_S_{style}_C_{color}_I_{item}".lower()
        # Add border flag.
        if img_has_borders:
            name += "_hasborder".lower()
        # Remove spaces and special characters, keep alphanumeric, underscores, and hyphens.
            name = re.sub(r'[^a-z0-9_-]', '', name)
        return f"{name}.png"
    except Exception as e:
        raise RuntimeError(f"Failed to create image name ({name}): {str(e)}")


def call_openai_img_endpoint(prompt):
    # Set Up OpenAI Endpoint
    client = AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version="2024-02-01"
    )
    # Call client endpoint to generate image.
    max_retries = 5 # Retry if timeout is reached.
    for attempt in range(max_retries):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024", # Only dall-e-3 supports non-square images.
                quality="standard", # dall-e-3 supports quality "hd" (on top of "standard").
                n=1, # Only dall-e-2 supports > 1 image per deployment.
                timeout=60
            )
            break  # Exit loop if successful
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout occurred at OpenAI img generation step, retrying... (Attempt {attempt + 1}/{max_retries})")
                continue  # Retry if not the last attempt
            else:
                raise RuntimeError(f"OpenAI image endpoint timed out after {max_retries} retries.")

    #image_url = json.loads(response.model_dump_json())['data'][0]['url']
    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt

    return image_url, revised_prompt


if __name__ == "__main__":

    image_url = "https://politikeaaihub3252052849.blob.core.windows.net/politikea-flags-20250214/20250307-144104-413505_e_waterfall_s_tribal_c_yellow_i_snake.png"
    #image_url = "flag_with_deer.png"
    # Download the image.
    image_data = requests.get(image_url).content
    #image = np.asarray(bytearray(image_data.read()), dtype="uint8")
    image = np.asarray(bytearray(image_data), dtype="uint8")
    #image = np.frombuffer(image_data, dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    #print(">>> IMAGE_DATA TYPE (REQUESTS):", type(image_data))
    #image = cv2.imread(image_url)
    #print(">>> IMAGE_DATA TYPE (CV2):", type(image_data))
    # Detect borders.
    img_has_borders, borders_sum, out_img = detect_borders(image)

    print(img_has_borders)
    print(borders_sum)

