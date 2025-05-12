#!/usr/bin/env python3

import requests
import json
import os
import re

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
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

# Function to extract and process data from a JSON file
def process_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

        # Check for errors in the JSON file
        if "error" in data:
            print(f"Error in file {file_path}: {data['error']}")
            return

        # Example processing logic
        # Extract headwords and translations from the JSON
        processed_data = []
        for language_entry in data:
            for hit in language_entry.get('hits', []):
                for rom in hit.get('roms', []):
                    headword = rom.get('headword', 'Unknown')
                    translations = [
                        translation.get('target', 'Unknown')
                        for arab in rom.get('arabs', [])
                        for translation in arab.get('translations', [])
                    ]
                    processed_data.append({
                        "headword": headword,
                        "translations": translations
                    })

        # Print the processed data
        print(json.dumps(processed_data, ensure_ascii=False, indent=4))

# Main workflow: Fetch and process
# Step 1: Read query terms from the input file and fetch data
with open(input_file_path, 'r', encoding='utf-8') as file:
    for line in file:
        query_term = line.strip()
        if query_term:
            fetch_and_save(query_term)

# Step 2: Process the saved JSON files
for filename in os.listdir(output_directory):
    if filename.endswith('.json'):
        process_json_file(os.path.join(output_directory, filename))