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
processed_file_path = os.path.join(base_directory, "processed.json")
schema_file_path = os.path.join(base_directory, "schema.json")
query_parts_of_speech_json_path = os.path.join(base_directory, "Query Parts of Speech.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{datetime.now().strftime('%Y%m%dT%H%M%S')}.xlsx")
schematic_file_path = os.path.join(base_directory, "schematic.json")

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Strings to be cut off during re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Summary data for logging
summary_data = Counter()

# Setup logging
logging.basicConfig(
    filename=os.path.join(base_directory, f"debug_{datetime.now().strftime('%Y%m%dT%H%M%S')}.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Script started")
logging.info(f"Mode: {mode}")

# Function to fetch data from the concatenated JSON file and save it in a processed format
def fetch():
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    with open(concatenated_file_path, "r", encoding="utf-8") as file:
        concatenated_data = json.load(file)

    with open(processed_file_path, "w", encoding="utf-8") as processed_file:
        json.dump(concatenated_data, processed_file, ensure_ascii=False, indent=4)

# Function to process the fetched JSON data
def process():
    if not os.path.exists(processed_file_path):
        print(f"Processed JSON file not found at {processed_file_path}. Please run 'fetch' mode first.")
        return

    with open(processed_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    processed_data = []
    regex_patterns = {
        "example_pattern_1": (
            r"<span class=\\"wordclass\\">([^<]+)</span>",
            lambda match: {"word_class": match.group(1)}
        ),
        "example_pattern_2": (
            r"<span class=\\"verbclass\\">([^<]+)</span>",
            lambda match: {"verb_class": match.group(1)}
        )
    }
    regex_replacements = {
        r"<acronym title=\\?\"([^<].*)\\?\">[^<].*</acronym>": r"\1",
        r"<strong class=\\?\"headword\\?\">([^<]+)</strong>": r"\1",
        r"<strong class=\\?\"tilde\\?\">([^<]+)</strong>": r"\1"
    }

    for entry in data:
        query = entry["query"]
        response_data = entry.get("data", {})
        if "error" in response_data:
            continue

        for language_entry in response_data.get("entries", []):
            for hit in language_entry.get("hits", []):
                for rom in hit.get("roms", []):
                    headword_full = rom.get("headword_full", "")
                    extracted_data, processed_text = extract_patterns(headword_full, regex_patterns)
                    rom.update(extracted_data)
                    rom["headword_full_after_regex"] = perform_replacements(processed_text, regex_replacements)

        processed_data.append(entry)

    with open(processed_file_path, "w", encoding="utf-8") as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)

# Function to extract patterns from text
def extract_patterns(text, patterns):
    extracted_data = {}
    remaining_text = text
    for key, (pattern, func) in patterns.items():
        matches = re.finditer(pattern, remaining_text)
        extracted_matches = [func(match) for match in matches]
        if extracted_matches:
            extracted_data[key] = extracted_matches if len(extracted_matches) > 1 else extracted_matches[0]
            remaining_text = re.sub(pattern, "", remaining_text, count=(1 if len(extracted_matches) == 1 else 0))
    return extracted_data, remaining_text.strip()

# Function to perform regex replacements
def perform_replacements(text, replacements):
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text

# Main workflow logic
if mode == "fetch":
    fetch()
elif mode == "process":
    process()
elif mode == "reconcile":
    print("Reconciliation process in progress...")
    # Add reconciliation logic here
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, reconcile, concatenate")
