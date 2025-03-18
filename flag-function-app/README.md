# 0. Prerrequesites: Azure Function

# 0.a. FULL Python Env Preparation

- Install azure-cli

```bash
brew install azure-cli
```

- Install Azure Functions Core Tools, if not installed (azure-functions-core-tools@4). *Resolves "FUNC is not recognized as a command".*


```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4
# windows
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

## 0.b. Minimal Python Env Preparation

Install azure-functions-core-tools@4 without "brew":
- Windows: https://github.com/Azure/azure-functions-core-tools#install-the-azure-functions-core-tools
- MacOS: `brew install azure-functions-core-tools@4
npm install -g azure-functions-core-tools@4`

Install Azure functions:

```bash
pip install azure-functions
```


# 1. Local Azure Function Setup

## 1.1. Initialize the Azure Function App

This is only needed once. It creates the `host.json` and `function.json` files.

- Remember, only have either `@app.route()` or `function.json`. Never both.

```bash
func init flag-function-app --python
cd flag-function-app
func new --name generate_flag --template "HTTP trigger" --authlevel "anonymous"
```

## 1.2. Test Function App Locally

- Start the function app locally (ensure local.settings.json has necessary env vars):

```bash
cd my-function-app
func start
```

- Test the function app locally:

```bash
curl -X POST "http://localhost:7071/api/generate_flag" \
     -H "Content-Type: application/json" \
     -d '{"element": "waterfall", "style": "tribal", "color": "yellow", "item": "snake"}' \
     -o flag_creation_response.json
```

Expected Response:

```json
{
  "image_url": "https://mystorageaccount.blob.core.windows.net/generated-images/orange_elephant_grass.png"
}
```

### 1.2.1 Test Batch Version Locally

Note, for the Batch version, you need to increase max-time so it doesn't break. Processing of image generation and border detection is currently ~30secs per image.

```bash
curl -X POST "http://localhost:7071/api/generate_batch_flags" \
     -H "Content-Type: application/json" \
     -d '{"n_flags": 10, "n_attempts": 1, "elements": ["River", "Waves", "Waterfall", "Mountain", "Desert", "Forest", "City", "Sky", "Pathway", "Horizon", "Sea", "Grass", "Moon ", "Starry night", "Sun", "Sunrise"], "styles": ["Tribal", "Pop art", "Line art", "Art nouveau", "Cubist"], "colors": ["Magenta", "Lime Green", "Mahogay Red", "Lemon Gold", "Navy Blue"], "items": ["Doplhin", "Beaver", "Hummingbird", "Otter", "Chamaleon", "Compass", "Flower", "Lighthouse", "Windmill", "Open hand"]}' \
     -o flag_batch_creation_response.json --max-time 400
```

# 2. Deploy to Azure

## 2.1. Prepare Azure Function App

NOTE, FUNCTION NAME CAN HAVE DASHES (-), but NOT underscores (_).

```bash
az login
az functionapp create --resource-group politikea-rg \
    --consumption-plan-location swedencentral \
    --runtime python \
    --runtime-version 3.9 \
    --os-type Linux \
    --functions-version 4 \
    --name flag-function-app \
    --storage-account politikeaaihub3252052849
```

*Only `create` the Function App ONCE. Subsequent pushes of new code do NOT require recreation.*

## 2.2. Publish Azure Function

Push latest version of the code to Azure for compilation.

```bash
# Build zip files.
# - alternatively, you can use "zip -r flag-function-app.zip ."
func pack --build-native-deps
# Push zipped files to the cloud.
az functionapp deployment source config-zip --resource-group politikea-rg --name flag-function-app --src flag-function-app.zip
```


## 2.3. Start Azure Function

- Every time you publish a new version, you will have to restart the app *(use "start" if not deployed already)*:

```bash
az functionapp start --name flag-function-app --resource-group politikea-rg
```

### 2.3.1. Restart Azure Function

If you have already started the function app once, you must `restart` moving forward.

- Note, you must restart the app every time you push a new ZIP file:

```bash
az functionapp restart --name flag-function-app --resource-group politikea-rg
```

## 2.4. Test Function App in Azure

Once deployed, you can call the function using Postman or cURL.

```bash
curl -X POST "https://flag-function-app.azurewebsites.net/api/generate_flag" \
     -H "Content-Type: application/json" \
     -d '{"element": "waterfall", "style": "tribal", "color": "yellow", "item": "snake"}' \
     -o flag_creation_response.json
```

Expected Response:

```json
{
  "image_url": "https://mystorageaccount.blob.core.windows.net/generated-images/orange_elephant_grass.png"
}
```

### 2.4.1 Test Batch version in Azure

```bash
curl -X POST "https://flag-function-app.azurewebsites.net/api/generate_batch_flags" \
     -H "Content-Type: application/json" \
     -d '{"n_flags": 10, "n_attempts": 1, "elements": ["River", "Waves", "Waterfall", "Mountain", "Desert", "Forest", "City", "Sky", "Pathway", "Horizon", "Sea", "Grass", "Moon ", "Starry night", "Sun", "Sunrise"], "styles": ["Tribal", "Pop art", "Line art", "Art nouveau", "Cubist"], "colors": ["Magenta", "Lime Green", "Mahogay Red", "Lemon Gold", "Navy Blue"], "items": ["Doplhin", "Beaver", "Hummingbird", "Otter", "Chamaleon", "Compass", "Flower", "Lighthouse", "Windmill", "Open hand"]}' \
     -o flag_batch_creation_response.json --max-time 400
```

# 3. Debug Azure Function App

## 3.1. Ensure App is Running

- Check the "Status". It should be "Running". *If this fails or returns an error like ResourceNotFound, then your function app isn't properly deployed.*

```bash
az functionapp show --name flag-function-app --resource-group politikea-rg
```

## 3.2. Debug Function Files

The best way to debug the Function App is with Azure Visual Code: Azure Function App Extension.

It will allow you to see the files, env vars, and functions in one place.

### 3.2.1 Open CMD Window from Kudu

If you prefer a GUI, you can explore files in Azure Kudu Console:

- Open your browser and go to:

```bash
https://flag-function-app.scm.azurewebsites.net
```

- Click on Debug Console → CMD

- Navigate to /home/site/wwwroot/ to see deployed files.

## 3.3. Stop Function App

Stop the functions to prevent any potential charges. Your app will remain deployed and can be restarted easily.

```bash
az functionapp stop --name flag-function-app --resource-group politikea-rg
```

* Use start to redeploy the function:

```bash
az functionapp start --name flag-function-app --resource-group politikea-rg
```

## 3.4. Delete Function App

You can always delete, and then recreate the function app to start from scratch. Deleting does require adding the env vars manually.

```bash
az functionapp delete --name flag-function-app --resource-group politikea-rg
```

# 4. SPECIFIC ERRORS HANDLED

## 4.1. Edit FunctionApp Env Variables in AZURE

You can use the CMD to see and retrieve Env Vars.

*Using Azure Function App Extension in Visual Studio Code is recommended.*

- Get Env Vars that have been already set:

```bash
az functionapp config appsettings list --name flag-function-app --resource-group politikea-rg
```

- Set new Env Vars (one or many):

```bash
az functionapp config appsettings set --name flag-function-app --resource-group politikea-rg \
    --settings AZURE_OPENAI_API_KEY="<YOUR-KEY>" \
    AZURE_OPENAI_ENDPOINT="<YOUR-ENDPOINT>"
```

*Restart the function app after setting new vars*.

## 4.2. Resolve error "The parameter WEBSITE_CONTENTSHARE has an invalid value."

- Check your storage account type. If the output is NOT 'Standard_LRS' or 'Premium_LRS', you need to create a new storage account:

```bash
az storage account show --name politikeaaihub3252052849 --resource-group politikea-rg --query "sku.name"
# (DO NOT RUN) Create new storage if your existing one wasn't of the correct type ('Standard_LRS' or 'Premium_LRS'):
az storage account create --name politikeastorage --resource-group politikea-rg --location swedencentral --sku Standard_LRS
```

- Check if the storage account exists and is correctly spelled:

```bash
az storage account list --resource-group politikea-rg --query "[].name"
```

- **Ensure that your Function App Name has DASHES (-) and NOT underscores (_)!**

## 4.3. (LOCAL) Ensure a Valid Connection to Storage

- Run this command to extract the necessary string:

```bash
az storage account show-connection-string --name politikeaaihub3252052849 --resource-group politikea-rg --query connectionString --output tsv
```

- Then, embed the output of the previous command into both the "AzureWebJobsStorage" & the "AZURE_STORAGE_CONNECTION_STRING" env vars in `local.settings.json`:

```json
"AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=YOUR_SUFFIX;[...]",
"AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=YOUR_SUFFIX;[...]"
```

## 4.4. NEVER 'Publish' the Function App

Note, Linux-Python runtimes do not permit PUBLISH method (files are deleted). We switched to ZIP upload instead.

```bash
func azure functionapp publish flag-function-app
# Verify the function app exists
az functionapp list --resource-group politikea-rg --query "[].name"
```