import os
import datetime
import re
import cv2
import requests
import random
import numpy as np
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient
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
            stored_image_url, img_has_borders = generate_and_store_flag(element, style, color, item)
            if not img_has_borders:
                return stored_image_url
        return stored_image_url

    except Exception as e:
        raise RuntimeError(f"Failed to batch img generation & storage: {str(e)}")


def generate_and_store_flag(element: str, style: str, color: str, item: str) -> str:
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
        image_url = create_flag(element, style, color, item)
        # Download the image.
        image_data = requests.get(image_url).content
        image = np.asarray(bytearray(image_data), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # Detect borders.
        img_has_borders, borders_sum, out_img = detect_borders(image)
        # Store img in azure.
        img_params = {
            "element": element,
            "style": style,
            "color": color,
            "item": item
        }
        stored_image_url = store_flag_image(image_data, img_params, img_has_borders)
        return stored_image_url, img_has_borders

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
        prompt = (
            f"I want a rectangular horizontal image. "
            f"It must have a {style} style. The image must not be too cluttered. "
            f"The image must be harmoniously balanced. The image must include: "
            f"- The color {color}; - A(n) {item}; - A(n) {element}."
        )
        # PROMPT REWRITING: https://platform.openai.com/docs/guides/images#dall-e-3-prompting
        base_prompt = "" #"I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"
        prompt = base_prompt + prompt
        # WHAT's NEW WITH DALL-E-3: https://cookbook.openai.com/articles/what_is_new_with_dalle_3
        
        image_url = call_openai_img_endpoint(prompt)
        return image_url
    
    except Exception as e:
        raise RuntimeError(f"Failed to generate image: {str(e)}")


def store_flag_image(image_data, img_params, img_has_borders=False) -> str:
    """
    Downloads an image from OpenAI and uploads it to Azure Blob Storage.

    Args:
        image_data (img_data): The generated image in raw bytes format, ready
                               for Azure Storage.

    Returns:
        str: The public URL of the stored image in Azure Blob Storage.
    """

    try:
        blob_url = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        container_name = os.getenv("CONTAINER_NAME")

        ## Download the image.
        #image_data = requests.get(image_url).content
        #image_name = "futuristic_city.png"
        image_name = create_img_name(img_params, img_has_borders)

        # Create a blob service client
        blob_service_client = BlobServiceClient.from_connection_string(blob_url)
        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=image_name)
        # Upload the created file
        blob_client.upload_blob(image_data, overwrite=True)

        # Construct the correct public URL
        blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{image_name}"

        return blob_url
    
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

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024", # Only dall-e-3 supports non-square images.
        quality="standard", # dall-e-3 supports quality "hd" (on top of "standard").
        n=1 # Only dall-e-2 supports > 1 image per deployment.
    )

    #image_url = json.loads(response.model_dump_json())['data'][0]['url']
    image_url = response.data[0].url

    return image_url


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

