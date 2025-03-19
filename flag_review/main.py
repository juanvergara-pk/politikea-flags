from argparse import ArgumentParser
import subprocess
import os
import time
import json
from config import load_env_vars
from LS_export_data_manually import export_tasks_and_annotations
from LS_load_project import load_labelstudio_project

def load_json_file(json_fn):
    json_dict = {}
    with open(json_fn, 'r') as f:
        json_dict = json.load(f)
    return json_dict


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port",
                        dest="port", default="8080",
                        help="Port number to use for the app")
    parser.add_argument("-d", "--debug",
                        dest="debug", default=False,
                        help="Debug flag")

    args = parser.parse_args()
    labelstudio_port = args.port
    debug = args.debug

    # Load env vars.
    load_env_vars()
    labelstudio_token = os.getenv("LABELSTUDIO_TOKEN")
    labelstudio_key = os.getenv("LABELSTUDIO_KEY")

    # RUN THE APP
    p = subprocess.Popen([f'label-studio start -p {labelstudio_port} --username andres.cardelus@politikea.io --password {labelstudio_key} --user-token {labelstudio_token}'], shell=True)
    # Wait for 10 secs for the app to start
    time.sleep(60)

    ## Get User Token
    #sp = subprocess.run(f"curl -H 'Authorization: Token {labelstudio_token}' -X GET 'http://localhost:8080/api/current-user/token' -o user_token_response.json", shell=True)
    ## Read user token
    #token_dict = load_json_file('user_token_response.json')
    #user_token = token_dict['token']

    load_labelstudio_project(debug)

    # Loop until the user presses Ctrl-C or the process ends
    try:
        p.wait()
    except KeyboardInterrupt:
        print("User interrupted the process.")
        p.terminate()
    print("Process ended.")
