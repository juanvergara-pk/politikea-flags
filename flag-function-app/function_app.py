import azure.functions as func
import logging
# Import the function from __init__.py
from flag_generation import main as flag_generation_main
from flag_generation import batch_flag_generation as flag_generation_batch

app = func.FunctionApp()


@app.function_name(name="generate_flag")
@app.route(route="generate_flag", auth_level=func.AuthLevel.ANONYMOUS)
def generate_flag(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger that calls the correct function inside flag_generation/__init__.py.
    """
    logging.info("Processing request via function_app.py...")
    return flag_generation_main(req)


@app.function_name(name="generate_batch_flags")
@app.route(route="generate_batch_flags", auth_level=func.AuthLevel.ANONYMOUS)
def generate_batch_flags(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger that calls the correct function inside flag_generation/__init__.py.
    """
    logging.info("Processing request via function_app.py...")
    return flag_generation_batch(req)
