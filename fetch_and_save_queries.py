import requests
import json
import os

# Path to the input file containing query terms
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
# Directory to save the JSON files
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Function to fetch and save raw API response
def fetch_and_save(term):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"
    headers = {
        "X-Secret": "XXX"
    }
    response = requests.get(url, headers=headers)

    # Create a JSON file for each term
    output_file_path = os.path.join(output_directory, f"{term}.json")
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        if response.status_code == 200:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
        else:
            error_message = {
                "error": f"Received status code {response.status_code}",
                "response_text": response.text
            }
            json.dump(error_message, json_file, ensure_ascii=False, indent=4)

# Read query terms from the file and fetch data
with open(input_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        query_term = line.strip()
        if query_term:
            fetch_and_save(query_term)
