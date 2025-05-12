#!/usr/bin/env python3

import requests
import json
import os
import re
import csv

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "reconcile"  # Change this value to "process", "concatenate", "schematize", or "reconcile" as needed

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'
concatenated_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/concatenated.json'
query_parts_of_speech_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Query Parts of Speech.json'
csv_output_file = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/reconciliation_results.csv'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Function to fetch data from the API
def fetch_and_save(term):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"
    headers = {
        "X-Secret": "XXX"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": f"Received status code {response.status_code}",
            "response_text": response.text
        }

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

    # Open the CSV file for writing
    with open(csv_output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        # Write the header row
        csvwriter.writerow([
            "Original Query", "Revised Query", "Original Part of Speech", "Revised Part of Speech",
            "Cutoff Type", "Cutoff Applied", "Original Status", "Revised Status", "Revised Result"
        ])

        # Iterate over the concatenated data to find entries matching the criteria
        for entry in concatenated_data:
            query = entry["query"]
            data = entry["data"]

            # Default values for fields
            revised_query = ""
            revised_part_of_speech = ""
            cutoff_type = ""
            cutoff_applied = ""
            revised_status = "Failure"
            revised_result = "No Match"

            # Check for "Received status code 204" and matching criteria
            if isinstance(data, dict) and "error" in data and "Received status code 204" in data["error"]:
                original_part_of_speech = bulgarian_to_pos.get(query, "Unknown")

                # Handle Verbs with cutoff logic
                if original_part_of_speech == "Verb":
                    for cutoff in cutoff_strings:
                        if query.endswith(cutoff):
                            # Modify the query by removing the cutoff string
                            revised_query = query[: -len(cutoff)].strip()
                            cutoff_type = "Verb Cutoff"
                            cutoff_applied = cutoff

                            # Re-run the query
                            revised_data = fetch_and_save(revised_query)

                            # Check if the revised query returned a valid result
                            if not (isinstance(revised_data, dict) and "error" in revised_data):
                                revised_status = "Success"
                                revised_result = "Match Found"
                                revised_part_of_speech = "Verb"
                            break  # Stop checking other cutoff strings for this query

                # Handle Adverbs and Unclassified Words ending in "но"
                elif original_part_of_speech in ["Adverb", "Unclassified Word"]:
                    if query.endswith("но"):
                        # Modify the query by replacing "но" with "ен"
                        revised_query = re.sub(r"но$", "ен", query)
                        cutoff_type = "Adverb Modification"
                        cutoff_applied = "но → ен"

                        # Re-run the query
                        revised_data = fetch_and_save(revised_query)

                        # Check if the revised query matches Part of Speech = Adjective
                        if not (isinstance(revised_data, dict) and "error" in revised_data):
                            revised_status = "Success"
                            revised_result = "Match Found"
                            revised_part_of_speech = "Adjective"

                # Write the row to the CSV file
                csvwriter.writerow([
                    query, revised_query, original_part_of_speech, revised_part_of_speech,
                    cutoff_type, cutoff_applied, "Received status code 204", revised_status, revised_result
                ])

    print(f"Reconciliation completed. Results saved to {csv_output_file}")

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