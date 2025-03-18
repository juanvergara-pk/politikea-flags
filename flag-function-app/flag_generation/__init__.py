import json
import azure.functions as func
import logging
from flag_generation.flag_creation import generate_and_store_flag  # Import from flag_creation.py
from flag_generation.flag_creation import create_batch_flags

#app = func.FunctionApp()
#@app.route(route="generate_flag", auth_level=func.AuthLevel.ANONYMOUS)
#def generate_flag(req: func.HttpRequest) -> func.HttpResponse:
def main(req: func.HttpRequest) -> func.HttpResponse:
    
    """
    Azure Function that receives flag generation parameters, 
    calls OpenAI's API, stores the image in Azure Blob Storage, 
    and returns the final URL.
    """
    logging.info("Processing a flag generation request inside flag_generation/__init__.py...")
    try:
        # Parse request body
        req_body = req.get_json()
        element = req_body.get("element", "").strip()
        style = req_body.get("style", "").strip()
        color = req_body.get("color", "").strip()
        item = req_body.get("item", "").strip()

        # Ensure all parameters are provided
        if not element or not style or not color or not item:
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters: element, style, color, item"}),
                mimetype="application/json",
                status_code=400
            )

        # Generate and store the image
        image_url = generate_and_store_flag(element, style, color, item)

        return func.HttpResponse(
            json.dumps({"image_url": image_url}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error generating flag: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

def batch_flag_generation(req: func.HttpRequest) -> func.HttpResponse:
    
    """
    Azure Function that receives flag generation parameters, 
    calls OpenAI's API several times in batch, then stores the
    image in Azure Blob Storage, and returns the final URL.
    """
    logging.info("Processing a batch flag generation request inside flag_generation/__init__.py...")
    try:
        # Parse request body
        req_body = req.get_json()
        n_flags = req_body.get("n_flags", 10)
        elements = req_body.get("elements", [])
        styles = req_body.get("styles", [])
        colors = req_body.get("colors", [])
        items = req_body.get("items", [])
        n_attempts = req_body.get("n_attempts", 1)
        
        # Ensure all parameters are provided
        if not n_flags or not elements or not styles or not colors or not items or not n_attempts:
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters: elements, styles, colors, items"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Generate and store the images
        image_urls = create_batch_flags(n_flags, elements, styles, colors, items, n_attempts)
        
        return func.HttpResponse(
            json.dumps({"image_urls": image_urls}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error generating flags: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )