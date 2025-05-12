#!/usr/bin/env python3

import os
import json
import re
import logging
from datetime import datetime
from collections import Counter

# Paths and directories
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
processed_file_path = os.path.join(base_directory, "processed.json")
output_directory = os.path.join(base_directory, "PONS json Files")

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join(output_directory, "PONSAPI.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Regex to identify and expand acronyms
ACRONYM_PATTERN = re.compile(r'<acronym title="([^"]*)">[^<]*</acronym>')


def expand_acronyms(text):
    """
    Expand all acronyms in the given text using regex.
    """
    if not text:
        return text
    return ACRONYM_PATTERN.sub(r'\1', text)


def expand_acronyms_in_entry(entry):
    """
    Recursively expand acronyms in the given JSON entry.
    """
    if isinstance(entry, dict):
        return {key: expand_acronyms_in_entry(value) for key, value in entry.items()}
    elif isinstance(entry, list):
        return [expand_acronyms_in_entry(item) for item in entry]
    elif isinstance(entry, str):
        return expand_acronyms(entry)
    else:
        return entry


def process_entries():
    """
    Process the concatenated.json file into processed.json.
    This step validates, expands acronyms, and enriches the data for subsequent reconciliation.
    """
    if not os.path.exists(concatenated_file_path):
        logging.error(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'fetch' mode first.")
        return

    try:
        # Load concatenated.json
        with open(concatenated_file_path, 'r', encoding='utf-8') as file:
            concatenated_data = json.load(file)

        processed_data = []
        for entry in concatenated_data:
            # Ensure each entry is a dictionary
            if isinstance(entry, dict):
                # Expand acronyms
                expanded_entry = expand_acronyms_in_entry(entry)

                # Validate entry
                query = expanded_entry.get("query", "")
                data = expanded_entry.get("data", {})
                is_valid = isinstance(data, dict) and not data.get("error") and data.get("response_text", "").strip()

                processed_data.append({
                    "query": query,
                    "is_valid": is_valid,
                    "data": data
                })
            else:
                logging.warning(f"Unexpected entry format: {entry}")

        # Write processed data to processed.json
        with open(processed_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(processed_data, outfile, ensure_ascii=False, indent=4)

        logging.info(f"Processing completed. Processed data saved to {processed_file_path}")

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")


# Main workflow
if __name__ == "__main__":
    process_entries()