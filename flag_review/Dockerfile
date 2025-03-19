FROM python:3.8.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
#COPY . /usr/src/app/.
#COPY main.py main.py
#COPY ./flag_review ./


# LABEL STUDIO
#CMD [ "python", "./your-daemon-or-script.py" ]
#CMD [ "label-studio", "start", "-p", "8080" ]
# 1. Use "sh -c" to properly interpret the command
#CMD ["sh", "-c", "label-studio start -p 8080"]
# (alternative) Create a default account during startup "--username USERNAME --password PASSWORD"
# -> https://labelstud.io/guide/signup#Create-an-account-through-the-command-line
# User volumes to persist data & users with Docker "-v <yourvolume>:/<yourdirectory>:latest"
# -> https://labelstud.io/guide/storedata#Persist-data-with-Docker
#CMD ["sh", "-c", "label-studio start --data-dir flag_review_vol:/label_studio/flag_review -p 8080"]
CMD ["sh", "-c", "python main.py -p 8080"]
# sh -c python main.py -p 8080