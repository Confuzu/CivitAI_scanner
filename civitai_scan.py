import requests
import urllib.parse
import csv
from tqdm import tqdm

type_base_statistics = {}

# Prompt user for username
username = input("Enter your username: ")

# Format the URL with username, types, and nsfw parameter
base_url = "https://civitai.com/api/v1/models"
params = {
    "username": username,
}
url = f"{base_url}?{urllib.parse.urlencode(params)}&nsfw=true"

# Set the headers
headers = {
    "Content-Type": "application/json"
}

# Function to make the API call and retrieve the JSON response
def get_json_response(url):
    response = requests.get(url, headers=headers)
    return response.json()

# Function to check for totalItems in JSON response metadata
def check_response_metadata(data):
    metadata = data.get('metadata')

    if metadata:
        total_items = metadata.get('totalItems')
        if total_items:
            print("Total Items:", total_items)

# Function to extract data from the JSON response
def extract_data(data):
    items = data['items']
    download_urls = []

    for item in items:
        item_id   = item['id']
        item_name = item['name']
        item_type = item['type']

        model_versions = item.get('modelVersions', [])
        for version in model_versions:
            model_version_id = version.get('id')
            model_version_name = version.get('name')
            base_model = version.get('baseModel')
            files = version.get('files', [])
            images = version.get('images', [])

            # Create Item Type and Base Model Statistics
            type_base = item_type + "-" + base_model
            if type_base in type_base_statistics:
                # If the "type_base"  is already in the dictionary, increment its count
                type_base_statistics[type_base] += 1
            else:
                # If the "type_base" is not in the dictionary, add it with a count of 1
                type_base_statistics[type_base] = 1

            for file in files:
                file_name = file.get('name', '')
                file_download_url = file.get('downloadUrl', '')

                image_url = ''
                if images:
                    image_url = images[0].get('url', '')

                model_url = f"https://civitai.com/models/{item_id}"
                model_version_url = f"https://civitai.com/models/{item_id}?modelVersionId={model_version_id}"

                download_url_data = {
                    "Author": username,
                    "Item Name": item_name,
                    "Model Version Name": model_version_name,
                    "Item Type": item_type,
                    "Base Model": base_model,
                    "File Name": file_name,
                    "Download URL": file_download_url,
                    "Model Image": image_url,
                    "Model Version URL": model_version_url
                }

                download_urls.append(download_url_data)

    return download_urls

# Function to write the data to a CSV file
def write_to_csv(data, filename):
    fieldnames = ["Author", "Item Name", "Model Version Name", "Item Type", "Base Model", "File Name", "Download URL", "Model Image", "Model Version URL"]

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Make the initial API call and retrieve the JSON response
data = get_json_response(url)

# Check response metadata
check_response_metadata(data)

# Extract data from the initial JSON response
download_urls = extract_data(data)

# Initialize progress bar
pbar = tqdm(desc="Processing Pages", unit="page")

# Iterate through subsequent pages until there are no more pages
while True:
    pbar.update(1)
    metadata = data.get('metadata', {})
    next_page_url = metadata.get('nextPage')
    
    if not next_page_url:
        break

    # Make the API call to the next page
    data = get_json_response(next_page_url)

    # Extract data from the JSON response
    download_urls += extract_data(data)

pbar.close()

# Write the data to a CSV file
output_filename = f"{username}_output.csv"
write_to_csv(download_urls, output_filename)

print(f"Data written to {output_filename} successfully.")

# Display the type_base_statistics
print("Model Statistics:")
for item, count in type_base_statistics.items():
    print(f"{item}: {count}")

