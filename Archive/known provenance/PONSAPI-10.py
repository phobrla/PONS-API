#!/usr/bin/env python3

import requests
import json
import os
import re

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize"
mode = "schematize"  # Change this value to "process", "concatenate", or "schematize" as needed

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'
concatenated_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/concatenated.json'
schema_output_file = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/schema.json'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Function to fetch and save raw API response
# NOTE: This function has been commented out to prevent accidental usage
'''
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
'''

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

# Function to concatenate all JSON files into a single pretty-printed JSON file
def concatenate_json_files_pretty():
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

    # Write the concatenated data to a pretty-printed JSON file
    with open(concatenated_file_path, 'w', encoding='utf-8') as out_file:
        json.dump(concatenated_data, out_file, ensure_ascii=False, indent=4)

    print(f"Pretty-printed concatenated JSON data saved to {concatenated_file_path}")

# Function to generate a data dictionary (schema) from the concatenated JSON file
def generate_schema():
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    # Load the concatenated JSON data
    with open(concatenated_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    schema = {}

    def explore_structure(obj, path=""):
        """Recursively explore the structure of an object to generate a schema."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                explore_structure(value, current_path)
        elif isinstance(obj, list):
            if path not in schema:
                schema[path] = {"type": "list", "examples": []}
            for item in obj[:5]:  # Limit to 5 examples to keep the schema concise
                explore_structure(item, path)
        else:
            if path not in schema:
                schema[path] = {"type": type(obj).__name__, "examples": []}
            if obj not in schema[path]["examples"] and len(schema[path]["examples"]) < 5:
                schema[path]["examples"].append(obj)

    # Explore the structure of the concatenated JSON data
    explore_structure(data)

    # Save the schema to a JSON file
    with open(schema_output_file, 'w', encoding='utf-8') as out_file:
        json.dump(schema, out_file, ensure_ascii=False, indent=4)

    print(f"Schema generated and saved to {schema_output_file}")

# Main workflow
if mode == "fetch":
    print("The 'fetch' mode is currently disabled to prevent accidental usage.")
elif mode == "process":
    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            process_json_file(os.path.join(output_directory, filename))
    print("Processing completed.")
elif mode == "concatenate":
    concatenate_json_files_pretty()
    print("Concatenation completed.")
elif mode == "schematize":
    generate_schema()
    print("Schematization completed.")
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, concatenate, schematize")