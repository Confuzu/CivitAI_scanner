import requests
import urllib.parse
import csv
from tqdm import tqdm

# Prompt user for username
username = input("Enter your username: ")

# Format the URL with username, types, and nsfw parameter
base_url = "https://civitai.com/api/v1/models"
params = {
    "username": username,
}
url = f"{base_url}?{urllib.parse.urlencode(params)}"

# Set the headers
headers = {
    "Content-Type": "application/json"
}

# Function to make the API call and retrieve the JSON response
def get_json_response(url):
    response = requests.get(url, headers=headers)
    return response.json()

# Function to check for totalItems and totalPages in JSON response metadata
def check_response_metadata(data):
    metadata = data.get('metadata')

    if metadata:
        total_items = metadata.get('totalItems')
        total_pages = metadata.get('totalPages')

        if total_items:
            print("Total Items:", total_items)
        if total_pages:
            print("Total Pages:", total_pages)

# Function to extract data from the JSON response
def extract_data(data):
    items = data['items']
    download_urls = []

    for item in items:
        item_name = item['name']
        item_type = item['type']

        model_versions = item.get('modelVersions', [])
        for version in model_versions:
            model_id = version.get('modelId')
            files = version.get('files', [])
            images = version.get('images', [])

            for file in files:
                file_name = file.get('name', '')
                file_download_url = file.get('downloadUrl', '')

                image_url = ''
                if images:
                    image_url = images[0].get('url', '')

                model_url = f"https://civitai.com/models/{model_id}"

                download_url_data = {
                    "Item Name": item_name,
                    "Item Type": item_type,
                    "File Name": file_name,
                    "Download URL": file_download_url,
                    "Model Image": image_url,
                    "Model URL": model_url
                }

                download_urls.append(download_url_data)

    return download_urls

# Function to write the data to a CSV file
def write_to_csv(data, filename):
    fieldnames = ["Item Name", "Item Type", "File Name", "Download URL", "Model Image", "Model URL"]

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

# Iterate through subsequent pages until the last page is reached
metadata = data.get('metadata')
total_pages = metadata.get('totalPages', 0)

for page in tqdm(range(2, total_pages + 1), desc="Processing Pages"):
    next_page_url = metadata.get('nextPage')
    if not next_page_url:
        break

    # Make the API call to the next page
    data = get_json_response(next_page_url)

    # Extract data from the JSON response
    download_urls += extract_data(data)

# Write the data to a CSV file
output_filename = f"{username}_output.csv"
write_to_csv(download_urls, output_filename)

print(f"Data written to {output_filename} successfully.")