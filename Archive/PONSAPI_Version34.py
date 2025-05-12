#!/usr/bin/env python3

import requests
import csv
import os
import re
import json
import logging
from datetime import datetime
from collections import Counter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from pyxlsb import open_workbook

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "reconcile"  # Default mode is set to "reconcile"

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# Paths and directories
input_file_path = os.path.join(base_directory, "Inputs_for_PONS_API.txt")
output_directory = os.path.join(base_directory, "PONS json Files")
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
schema_file_path = os.path.join(base_directory, "schema.json")
query_parts_of_speech_json_path = os.path.join(base_directory, "Query Parts of Speech.json")

# Generate the timestamp suffix
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
csv_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.csv")
log_file_path = os.path.join(base_directory, f"debug_{timestamp}.log")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.xlsx")

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

# Strings to be cut off during re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Summary data for logging
summary_data = Counter()

# Toggle to control whether to return the raw API response
return_raw_api_response = True

# Array for the queries
query_terms = ["искам", "харесвам"]

# Function to extract patterns from the text
def extract_patterns(text, patterns):
    extracted_data = {}
    remaining_text = text
    for key, (pattern, func) in patterns.items():
        matches = re.finditer(pattern, remaining_text)
        extracted_matches = [func(match) for match in matches]
        if extracted_matches:
            extracted_data[key] = extracted_matches if len(extracted_matches) > 1 else extracted_matches[0]
            remaining_text = re.sub(pattern, '', remaining_text, count=(1 if len(extracted_matches) == 1 else 0))
    return extracted_data, remaining_text.strip()

# Function to fetch dictionary data
def fetch_dictionary_data(term):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"  # Define the URL for the API request
    headers = {
        "X-Secret": "XXX"  # Define the headers with the secret key
    }
    response = requests.get(url, headers=headers)  # Make a GET request to the API with the headers

    if return_raw_api_response:
        if response.status_code == 200:
            print(json.dumps(response.json(), ensure_ascii=False, indent=4))
        else:
            print(f"Error: Received status code {response.status_code}")
        return

    if response.status_code == 200:  # Check if the response status code is 200 (OK)
        response_json = response.json()  # Parse the response JSON

        # Dictionary for regex patterns
        regex_patterns = {
            'conjugation1': r'<span class="conjugation"><acronym title="([^"]+)">[^<]*</acronym></span>',  # Updated to match the first instance
            'conjugation2': r', <span class="headword">[^<]+</span> <span class="conjugation"><acronym title="([^"]+)">[^<]+</acronym></span>',
            'word_class': r'<span class="wordclass">([^<]+)</span>',
            'verb_class': r'<span class="verbclass"><acronym title="([^"]+)">[^<]+</acronym></span>',
            'headword': r'<strong class="headword">([^<]+)</strong>'
        }

        # Dictionary for regex replacements
        regex_replacements = {
            r'<acronym title=\\?"([^<].*)\\?">[^<].*</acronym>': r'\1',  # Define regex pattern to replace <acronym> tags with their title attribute values
            r'<strong class=\\?"headword\\?">([^<]+)</strong>': r'\1',  # Define regex pattern to remove <strong class="headword"> tags, leaving only the text
            r'<strong class=\\?"tilde\\?">([^<]+)</strong>': r'\1'  # Define regex pattern to remove <strong class="tilde"> tags, leaving only the text
        }

        # Function to perform regex replacements on a string
        def perform_replacements(text):
            for pattern, replacement in regex_replacements.items():
                text = re.sub(pattern, replacement, text)
            return text

        # Filter out entries with <span class="example"> and sources other than <strong class="headword"></strong>
        for language_entry in response_json:  # Loop through each language entry in the response
            for hit in language_entry.get('hits', []):  # Loop through each hit in the language entry
                for level_one in hit.get('roms', []):  # Loop through each level one in the hit
                    # Extract conjugation information
                    conjugation_match = re.search(regex_patterns['conjugation1'], level_one.get('headword_full', ''))  # Search for the regex pattern in the 'headword_full' field
                    if conjugation_match:  # Check if there is a match
                        conjugation = conjugation_match.group(1)  # Extract the conjugation from the match
                        level_one['conjugation1'] = conjugation  # Add the conjugation to the level one dictionary
        # Additional functionality to extract patterns and aggregate data
        aggregated_data = []
        print(json.dumps(aggregated_data, ensure_ascii=False, indent=4))
        
    else:
        print(f"Error: Received status code {response.status_code}")

if __name__ == "__main__":
    for term in query_terms:
        fetch_dictionary_data(term)  # Call the function for each query term