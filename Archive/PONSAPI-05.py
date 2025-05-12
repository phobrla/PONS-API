#!/usr/bin/env python3

import requests
import json
import os
import re

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate"
mode = "fetch"  # Change this value to "process" or "concatenate" as needed

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'
concatenated_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/concatenated_minified.json'

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

# Function to concatenate all JSON files into a single minified JSON file
def concatenate_json_files_minified():
    concatenated_data = []

    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # Add the filename (minus .json) as a top-level field
                data_with_query = {
                    "query": filename[:-5],  # Remove ".json"
                    "data": data
                }
                concatenated_data.append(data_with_query)

    # Write the concatenated data to a single minified JSON file
    with open(concatenated_file_path, 'w', encoding='utf-8') as out_file:
        json.dump(concatenated_data, out_file, ensure_ascii=False, separators=(',', ':'))

    print(f"Minified concatenated JSON data saved to {concatenated_file_path}")

# Main workflow
if mode == "fetch":
    with open(input_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            query_term = line.strip()
            if query_term:
                fetch_and_save(query_term)
    print("Fetching and saving completed.")
elif mode == "process":
    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            process_json_file(os.path.join(output_directory, filename))
    print("Processing completed.")
elif mode == "concatenate":
    concatenate_json_files_minified()
    print("Concatenation completed.")
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, concatenate")