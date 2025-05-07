#!/usr/bin/env python3

import requests
import csv
import os
import re
import json

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "reconcile"  # Change this value to "fetch", "process", "concatenate", "schematize", or "reconcile" as needed

# Paths and directories
input_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Inputs_for_PONS_API.txt'
output_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'
concatenated_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/concatenated.json'
schema_file_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/schema.json'
query_parts_of_speech_csv_path = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/Query Parts of Speech.csv'
csv_output_file = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/reconciliation_results.csv'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Function to fetch data from the API
def fetch_entries():
    if not os.path.exists(input_file_path):
        print(f"Input file not found at {input_file_path}. Please provide a valid input file.")
        return

    # Read the input terms
    with open(input_file_path, 'r', encoding='utf-8') as file:
        terms = [line.strip() for line in file if line.strip()]

    # Fetch data from the API for each term
    for term in terms:
        url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"
        headers = {
            "X-Secret": "XXX"
        }
        response = requests.get(url, headers=headers)

        # Save the response to a JSON file
        output_file_path = os.path.join(output_directory, f"{term}.json")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            if response.status_code == 200:
                json.dump(response.json(), output_file, indent=4, ensure_ascii=False)
            else:
                json.dump({
                    "error": f"Received status code {response.status_code}",
                    "response_text": response.text
                }, output_file, indent=4, ensure_ascii=False)

    print(f"Fetch completed. Results saved to {output_directory}")

# Function to process individual JSON files
def process_entries():
    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Example processing logic
            # Add your specific processing logic here
            processed_data = {
                "term": filename.replace(".json", ""),
                "response": data
            }

            # Save the processed data back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(processed_data, file, indent=4, ensure_ascii=False)

    print(f"Processing completed. Files updated in {output_directory}")

# Function to concatenate JSON files into a single file
def concatenate_entries():
    concatenated_data = []

    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                concatenated_data.append(data)

    with open(concatenated_file_path, 'w', encoding='utf-8') as file:
        json.dump(concatenated_data, file, indent=4, ensure_ascii=False)

    print(f"Concatenation completed. Results saved to {concatenated_file_path}")

# Function to generate a schema from concatenated JSON
def generate_schema():
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    with open(concatenated_file_path, 'r', encoding='utf-8') as file:
        concatenated_data = json.load(file)

    # Example schema generation logic
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {}
        }
    }

    for entry in concatenated_data:
        for key, value in entry.items():
            if key not in schema["items"]["properties"]:
                schema["items"]["properties"][key] = {"type": type(value).__name__}

    with open(schema_file_path, 'w', encoding='utf-8') as file:
        json.dump(schema, file, indent=4, ensure_ascii=False)

    print(f"Schema generation completed. Results saved to {schema_file_path}")

# Function to reconcile specific cases in the concatenated JSON
def reconcile_entries():
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    if not os.path.exists(query_parts_of_speech_csv_path):
        print(f"Query Parts of Speech CSV file not found at {query_parts_of_speech_csv_path}. Please ensure it exists.")
        return

    # Load the concatenated JSON data
    with open(concatenated_file_path, 'r', encoding='utf-8') as file:
        concatenated_data = json.load(file)

    # Load the Query Parts of Speech CSV file
    bulgarian_to_pos = {}
    with open(query_parts_of_speech_csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            bulgarian_word = row.get("Bulgarian", "").strip()
            part_of_speech = row.get("Part of Speech", "").strip()
            if bulgarian_word and part_of_speech:
                bulgarian_to_pos[bulgarian_word] = part_of_speech

    # Open the CSV file for writing
    with open(csv_output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        # Write the header row
        csvwriter.writerow([
            "Original Query", "Revised Query", "Original Part of Speech", "Cutoff Type",
            "Cutoff Applied", "Original Status", "Revised Status", "Revised Result"
        ])

        # Iterate over the concatenated data to find entries matching the criteria
        for entry in concatenated_data:
            query = entry["query"]
            original_data = entry.get("data", None)

            # Default values for fields
            revised_query = ""
            cutoff_type = ""
            cutoff_applied = ""
            revised_status = "Failure"
            revised_result = "No Match"

            # Part of Speech
            original_part_of_speech = bulgarian_to_pos.get(query, "Unknown")

            # Handle Verbs with cutoff logic
            if original_part_of_speech == "Verb":
                for cutoff in cutoff_strings:
                    if query.endswith(cutoff):
                        # Modify the query by removing the cutoff string
                        revised_query = query[: -len(cutoff)].strip()
                        cutoff_type = "Verb Cutoff"
                        cutoff_applied = cutoff

                        # Check if the revised query exists in the concatenated data
                        revised_entry = next((e for e in concatenated_data if e["query"] == revised_query), None)
                        if revised_entry and revised_entry.get("data"):
                            revised_status = "Success"
                            revised_result = "Match Found"
                        break  # Stop checking other cutoff strings for this query

            # Handle Adverbs and Unclassified Words ending in "но"
            elif original_part_of_speech in ["Adverb", "Unclassified Word"]:
                if query.endswith("но"):
                    # Modify the query by replacing "но" with "ен"
                    revised_query = re.sub(r"но$", "ен", query)
                    cutoff_type = "Adverb Modification"
                    cutoff_applied = "но → ен"

                    # Check if the revised query exists in the concatenated data
                    revised_entry = next((e for e in concatenated_data if e["query"] == revised_query), None)
                    if revised_entry and revised_entry.get("data"):
                        revised_status = "Success"
                        revised_result = "Match Found"

            # Write the row to the CSV file
            csvwriter.writerow([
                query, revised_query, original_part_of_speech,
                cutoff_type, cutoff_applied, "Processed", revised_status, revised_result
            ])

    print(f"Reconciliation completed. Results saved to {csv_output_file}")

# Main workflow
if mode == "fetch":
    fetch_entries()
elif mode == "process":
    process_entries()
elif mode == "concatenate":
    concatenate_entries()
elif mode == "schematize":
    generate_schema()
elif mode == "reconcile":
    reconcile_entries()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, concatenate, schematize, reconcile")