#!/usr/bin/env python3

import requests
import csv
import os
import re
import json
import logging
from datetime import datetime

# Selector to choose the function to run
# Options: "locked", "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "locked"  # Default mode is "locked" to prevent accidental usage

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# Paths and directories
input_file_path = os.path.join(base_directory, "Inputs_for_PONS_API.txt")
output_directory = os.path.join(base_directory, "PONS json Files")
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
schema_file_path = os.path.join(base_directory, "schema.json")
query_parts_of_speech_csv_path = os.path.join(base_directory, "Query Parts of Speech.csv")

# Generate the timestamp suffix
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
csv_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.csv")
log_file_path = os.path.join(base_directory, f"debug_{timestamp}.log")

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Setup logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Script started")
logging.info(f"Mode: {mode}")
logging.info(f"CSV Output File: {csv_output_file}")
logging.info(f"Log File: {log_file_path}")

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Function for locked mode
def locked_mode():
    logging.info("Locked mode activated. No operations will be performed.")
    print("The script is in 'locked' mode. No operations will be performed.")

# Function to fetch data from the API
def fetch_entries():
    logging.info("Fetch mode is currently disabled.")
    print("The 'fetch' mode is currently disabled to prevent accidental usage.")

# Function to process individual JSON files
def process_entries():
    logging.info("Starting process mode.")
    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            logging.debug(f"Processing file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Example processing logic
            processed_data = {
                "term": filename.replace(".json", ""),
                "response": data
            }

            # Save the processed data back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(processed_data, file, indent=4, ensure_ascii=False)
            logging.info(f"Processed and updated file: {file_path}")

    print(f"Processing completed. Files updated in {output_directory}")
    logging.info("Process mode completed.")

# Function to concatenate JSON files into a single file
def concatenate_entries():
    logging.info("Starting concatenate mode.")
    concatenated_data = []

    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            logging.debug(f"Reading file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                concatenated_data.append(data)

    with open(concatenated_file_path, 'w', encoding='utf-8') as file:
        json.dump(concatenated_data, file, indent=4, ensure_ascii=False)
    logging.info(f"Concatenated data written to: {concatenated_file_path}")
    print(f"Concatenation completed. Results saved to {concatenated_file_path}")

# Function to generate a schema from concatenated JSON
def generate_schema():
    logging.info("Starting schematize mode.")
    if not os.path.exists(concatenated_file_path):
        logging.error(f"Concatenated JSON file not found at: {concatenated_file_path}")
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
    logging.info(f"Schema generated and written to: {schema_file_path}")
    print(f"Schema generation completed. Results saved to {schema_file_path}")

# Function to reconcile specific cases in the concatenated JSON
def reconcile_entries():
    logging.info("Starting reconcile mode.")
    if not os.path.exists(concatenated_file_path):
        logging.error(f"Concatenated JSON file not found at: {concatenated_file_path}")
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    if not os.path.exists(query_parts_of_speech_csv_path):
        logging.error(f"Query Parts of Speech CSV file not found at: {query_parts_of_speech_csv_path}")
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
    logging.info("Loaded Query Parts of Speech mappings.")

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
            if original_part_of_speech == "Unknown":
                logging.warning(f"Part of Speech for query '{query}' is unknown.")

            # Handle Verbs with cutoff logic
            if original_part_of_speech == "Verb":
                for cutoff in cutoff_strings:
                    if query.endswith(cutoff):
                        revised_query = query[: -len(cutoff)].strip()
                        cutoff_type = "Verb Cutoff"
                        cutoff_applied = cutoff
                        revised_entry = next((e for e in concatenated_data if e["query"] == revised_query), None)
                        if revised_entry and revised_entry.get("data"):
                            revised_status = "Success"
                            revised_result = "Match Found"
                        break

            # Handle Adverbs and Unclassified Words ending in "но"
            elif original_part_of_speech in ["Adverb", "Unclassified Word"]:
                if query.endswith("но"):
                    revised_query = re.sub(r"но$", "ен", query)
                    cutoff_type = "Adverb Modification"
                    cutoff_applied = "но → ен"
                    revised_entry = next((e for e in concatenated_data if e["query"] == revised_query), None)
                    if revised_entry and revised_entry.get("data"):
                        revised_status = "Success"
                        revised_result = "Match Found"

            # Write the row to the CSV file
            csvwriter.writerow([
                query, revised_query, original_part_of_speech,
                cutoff_type, cutoff_applied, "Processed", revised_status, revised_result
            ])
            logging.debug(f"Processed query '{query}': Revised Query='{revised_query}', Revised Status='{revised_status}'")

    logging.info(f"Reconciliation completed. Results saved to {csv_output_file}")
    print(f"Reconciliation completed. Results saved to {csv_output_file}")

# Main workflow
if mode == "locked":
    locked_mode()
elif mode == "fetch":
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
    logging.error(f"Unknown mode: {mode}")
    print(f"Unknown mode: {mode}")
    print("Available modes: locked, fetch, process, concatenate, schematize, reconcile")