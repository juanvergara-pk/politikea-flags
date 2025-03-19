# VALIDATING FLAGS WITH LABEL-STUDIO

## 1. USERS - RUN THE CONTAINER LOCALLY

### 1.1. SETUP LOCAL CONTAINER

FIRST, UNZIP FILE `flag_review_docker.zip`.

SECOND, BUILD LATEST CODE INTO DOCKER CONTAINER:
```bash
docker build -t juanvergarapk/flag_review:latest .
```

### 1.2. RUN LOCAL CONTAINER

RUN THE LOCAL CONTAINER
[https://docs.docker.com/engine/network/#published-ports]

```bash
# Start Docker Image
docker run -it -p 0.0.0.0:8080:8080 juanvergarapk/flag_review:latest bash
# Load Label Studio (inside Docker container)
python main.py
```

### 1.3. EXPORT NEW LABELS MANUALLY

```bash
# Connect to Docker container runtime.
docker ps
docker exec -it <container-id> bash
# Run export command.
python LS_export_data_manually.py
```

### 1.4. IMPORT NEW CREATED IMAGES MANUALLY

```bash
# Connect to Docker container runtime.
docker ps
docker exec -it <container-id> bash
# Run import command.
python LS_import_new_tasks.py
```

## 2. DEVS - SETUP CONTAINER

- Share Docker Image as ZIP file:

```bash
# Save all files to ZIP file.
zip -r flag_review_docker.zip . -x flag_review_docker.tar -x flag_review_docker.zip
```

- Test Files before Sharing:

```bash
# Unzip files.
# Load unzipped files to Docker.
docker build -t juanvergarapk/flag_review:latest .
```

### Unused Alternative Methods

- Share Docker Image as TAR file. Unused because it creates heavy files!

```bash
# Docker save Latest Image.
docker save -o flag_review_docker.tar juanvergarapk/flag_review:latest
# Load shared image file.
docker load -i flag_review_docker.tar
```

- Share Docker Image using Docker Hub. Unused because it requires PAID plan!

```bash
# Push the latest image.
docker login
docker push juanvergarapk/flag_review:latest
# Pull the image from shared collaborator (requires PAID plan).
docker pull juanvergarapk/flag_review:latest
```


## 3. DEVS - SETUP AZURE STORAGE ACCOUNT

In order to be able to show the images in Label Studio you have to set up the Azure Storage Account. You shall add a rule to allow access from external IPs:

https://docs.humansignal.com/guide/storage#Prerequisites-1

1. Go to Azure Portal.
2. Open your Storage Account.
3. In the left pane, go to Settings > Resource Sharing (CORS)
4. Add a new rule that allows:
  - Allowed Origins: *
  - Allowed Methods: GET
  - Allowed Headers: *
  - Exposed Headers: Access-Control-Allow-Origin
  - Max Age: 3600
