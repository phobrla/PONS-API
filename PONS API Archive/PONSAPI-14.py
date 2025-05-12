#!/usr/bin/env python3

import requests
import json
import os
import re

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "reconcile"  # Change this value to "process", "concatenate", "schematize", or "reconcile" as needed

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'
concatenated_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/concatenated.json'
schema_output_file = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/schema.json'
query_parts_of_speech_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Query Parts of Speech.json'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Function to fetch data from the API
def fetch_and_save(term, output_file_path):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"
    headers = {
        "X-Secret": "XXX"
    }
    response = requests.get(url, headers=headers)

    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        if response.status_code == 200:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
        else:
            error_message = {
                "error": f"Received status code {response.status_code}",
                "response_text": response.text
            }
            json.dump(error_message, json_file, ensure_ascii=False, indent=4)

# Function to reconcile specific cases in the concatenated JSON
def reconcile_entries():
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    if not os.path.exists(query_parts_of_speech_path):
        print(f"Query Parts of Speech file not found at {query_parts_of_speech_path}. Please ensure it exists.")
        return

    # Load the concatenated JSON data
    with open(concatenated_file_path, 'r', encoding='utf-8') as file:
        concatenated_data = json.load(file)

    # Load the Query Parts of Speech data
    with open(query_parts_of_speech_path, 'r', encoding='utf-8') as file:
        query_parts_of_speech = json.load(file)

    # Create a mapping from "Bulgarian" field to "Part of Speech"
    bulgarian_to_pos = {}
    for entry in query_parts_of_speech:
        # Split by commas if multiple variations exist
        bulgarian_variations = [variant.strip() for variant in entry["Bulgarian"].split(",")]
        for variation in bulgarian_variations:
            bulgarian_to_pos[variation] = entry["Part of Speech"]

    # Iterate over the concatenated data to find entries matching the criteria
    for entry in concatenated_data:
        query = entry["query"]
        data = entry["data"]

        # Check for "Received status code 204" and matching criteria
        if isinstance(data, dict) and "error" in data and "Received status code 204" in data["error"]:
            # Handle Verbs with cutoff logic
            if query in bulgarian_to_pos and bulgarian_to_pos[query] == "Verb":
                for cutoff in cutoff_strings:
                    if query.endswith(cutoff):
                        # Modify the query by removing the cutoff string
                        revised_query = query[: -len(cutoff)].strip()

                        # Re-run the query
                        output_file_path = os.path.join(output_directory, f"{revised_query}.json")
                        fetch_and_save(revised_query, output_file_path)

                        # Check if the new query returned a valid result
                        with open(output_file_path, 'r', encoding='utf-8') as revised_file:
                            revised_data = json.load(revised_file)

                            if not (isinstance(revised_data, dict) and "error" in revised_data):
                                print(f"Revised query '{revised_query}' for original query '{query}' succeeded.")
                            else:
                                print(f"Revised query '{revised_query}' for original query '{query}' still failed.")
                        break  # Stop checking other cutoff strings for this query
            
            # Handle Adverbs and Unclassified Words ending in "но"
            elif query in bulgarian_to_pos and bulgarian_to_pos[query] in ["Adverb", "Unclassified Word"]:
                if query.endswith("но"):
                    # Modify the query by replacing "но" with "ен"
                    revised_query = re.sub(r"но$", "ен", query)

                    # Re-run the query
                    output_file_path = os.path.join(output_directory, f"{revised_query}.json")
                    fetch_and_save(revised_query, output_file_path)

                    # Check if the new query matches Part of Speech = Adjective
                    with open(output_file_path, 'r', encoding='utf-8') as revised_file:
                        revised_data = json.load(revised_file)

                        if not (isinstance(revised_data, dict) and "error" in revised_data):
                            print(f"Revised query '{revised_query}' for original query '{query}' succeeded as Adjective.")
                        else:
                            print(f"Revised query '{revised_query}' for original query '{query}' still failed.")

    print("Reconciliation completed.")

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
elif mode == "reconcile":
    reconcile_entries()
    print("Reconciliation completed.")
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, concatenate, schematize, reconcile")