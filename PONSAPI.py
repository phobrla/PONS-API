#!/usr/bin/env python3

import requests
import os
import re
import json
import logging
from datetime import datetime
from collections import Counter
from openpyxl import load_workbook, Workbook

# Selector to choose the function to run
# Options: "fetch", "process"
mode = "process"  # Default mode is set to "process"

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# Paths and directories
input_file_path = os.path.join(base_directory, "Inputs_for_PONS_API.txt")
output_directory = os.path.join(base_directory, "PONS json Files")
concatenated_file_path = os.path.join(output_directory, "concatenated.json")
query_parts_of_speech_json_path = os.path.join(base_directory, "Query Parts of Speech.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
xlsx_output_file = os.path.join(base_directory, "Reconciled_Results.xlsx")

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


def fetch_and_concatenate():
    """
    Fetches data from the PONS API for each query term and concatenates all results into a single JSON file.
    """
    concatenated_data = []

    with open(input_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            query_term = line.strip()
            if query_term:
                url = f"https://api.pons.com/v1/dictionary?q={query_term}&l=bgen"
                headers = {
                    "X-Secret": "XXX"
                }
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    concatenated_data.append({
                        "query": query_term,
                        "data": response.json()
                    })
                else:
                    concatenated_data.append({
                        "query": query_term,
                        "data": {
                            "error": f"Received status code {response.status_code}",
                            "response_text": response.text
                        }
                    })

    # Save the concatenated data to a single JSON file
    with open(concatenated_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(concatenated_data, output_file, ensure_ascii=False, indent=4)

    print(f"All data fetched and concatenated into {concatenated_file_path}")


def extract_patterns(text, patterns):
    """
    Extracts patterns from the given text using regular expressions.

    Args:
        text (str): The text to search for patterns.
        patterns (dict): A dictionary of patterns and associated functions.

    Returns:
        dict: A dictionary with extracted data and the remaining text.
    """
    result = {}
    for key, (pattern, func) in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = func(match)
            text = re.sub(pattern, '', text)
    result['text'] = text.strip()
    return result


def process_and_reconcile():
    """
    Processes entries from concatenated.json, reconciles them with Flashcards.xlsb,
    and saves the combined results into the 'processed' tab of Flashcards.xlsb.
    """
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'fetch' mode first.")
        return

    if not os.path.exists(flashcards_xlsb_path):
        print(f"Flashcards.xlsb file not found at {flashcards_xlsb_path}. Please ensure it exists.")
        return

    try:
        # Load concatenated.json
        with open(concatenated_file_path, 'r', encoding='utf-8') as file:
            concatenated_data = json.load(file)

        # Load Anki table from Flashcards.xlsb
        workbook = load_workbook(flashcards_xlsb_path, data_only=True)
        anki_sheet = workbook["Anki"]

        # Collect Anki data
        anki_data = []
        for row in anki_sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
            anki_data.append({
                "Bulgarian 1": row[0],
                "Bulgarian 2": row[1],
                "Part of Speech": row[2],
                "Note ID": row[3]
            })

        processed_data = []
        results = []

        # Matching logic
        for anki_row in anki_data:
            bulgarian_1 = anki_row["Bulgarian 1"]
            part_of_speech = anki_row["Part of Speech"]

            match_level = "No Match"
            matched_value = None
            cutoff_applied = None

            for json_entry in concatenated_data:
                query = json_entry["query"]
                data = json_entry.get("data", {})

                # Level 1: Exact match with matching wordclass
                if bulgarian_1 == query:
                    for rom in extract_roms(data):
                        wordclass = extract_wordclass(rom)
                        if wordclass == part_of_speech:
                            match_level = "1"
                            matched_value = query
                            break

                # Level 2: Exact match but mismatched wordclass
                if match_level == "No Match" and bulgarian_1 == query:
                    match_level = "2"
                    matched_value = query
                    break

                # Level 3: Various partial matches
                if match_level == "No Match":
                    match_level, matched_value = match_partial(bulgarian_1, data)

            # Level 4: Apply cutoff logic
            if match_level == "No Match":
                cutoff_applied, revised_query = apply_cutoff_logic(bulgarian_1)
                for json_entry in concatenated_data:
                    if revised_query == json_entry["query"]:
                        match_level = "4"
                        matched_value = revised_query
                        break

            # Append results
            results.append({
                "Bulgarian 1": bulgarian_1,
                "Match Level": match_level,
                "Matched Value": matched_value,
                "Cutoff Applied": cutoff_applied
            })

        # Save results
        save_results_to_excel(results, xlsx_output_file)
        print(f"Results saved to {xlsx_output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Extract ROMS from JSON data
def extract_roms(data):
    hits = data.get("hits", [])
    for hit in hits:
        for rom in hit.get("roms", []):
            yield rom


# Extract wordclass from headword_full
def extract_wordclass(rom):
    headword_full = rom.get("headword_full", "")
    match = re.search(r'<span class="wordclass">([^<]+)</span>', headword_full)
    return match.group(1) if match else None


# Match partial fields
def match_partial(bulgarian_1, data):
    for rom in extract_roms(data):
        header = rom.get("header", "")
        source = rom.get("source", "")

        # Match partial fields
        partial_matches = [
            (r'<span class="indirect_reference_OTHER">([^<]+)</span>', "3b"),
            (r'<span class="indirect_reference_RQ">([^<]+)</span>', "3c"),
            (r'<span class="full_collocation">([^<]+)</span>', "3d"),
            (r'<span class="reflection">([^<]+)</span>', "3e"),
        ]

        for pattern, level in partial_matches:
            match = re.search(pattern, header) or re.search(pattern, source)
            if match and bulgarian_1 == match.group(1):
                return level, match.group(1)

    return "No Match", None


# Apply cutoff logic
def apply_cutoff_logic(bulgarian_1):
    for cutoff in cutoff_strings:
        if bulgarian_1.endswith(cutoff):
            revised_query = bulgarian_1[: -len(cutoff)].strip()
            return cutoff, revised_query
    return None, None


# Save results to Excel
def save_results_to_excel(results, output_file):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reconciled Results"

    # Write header
    headers = ["Bulgarian 1", "Match Level", "Matched Value", "Cutoff Applied"]
    sheet.append(headers)

    # Write rows
    for result in results:
        sheet.append([result["Bulgarian 1"], result["Match Level"], result["Matched Value"], result["Cutoff Applied"]])

    # Save workbook
    workbook.save(output_file)


# Main workflow logic
if mode == "fetch":
    fetch_and_concatenate()
elif mode == "process":
    process_and_reconcile()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process")
