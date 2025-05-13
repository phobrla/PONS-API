#!/usr/bin/env python3

import requests
import os
import re
import json
import logging
from datetime import datetime
from collections import Counter
from openpyxl import load_workbook

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

        processed_data = []

        # Process each language entry in the concatenated data
        for lang_entry in concatenated_data:
            lang_data = {
                "lang": lang_entry.get("lang", ""),
                "hits": []
            }

            for hit in lang_entry.get('data', {}).get('hits', []):
                hit_data = {
                    "type": hit.get("type", ""),
                    "opendict": hit.get("opendict", False),
                    "roms": []
                }

                for rom in hit.get('roms', []):
                    rom_data = {
                        "headword": rom.get("headword", ""),
                        "headword_full": rom.get("headword_full", ""),
                        "wordclass": rom.get("wordclass", ""),
                        "conjugation": "",
                        "verbclass": "",
                        "arabs": []
                    }

                    # Extract conjugation and verbclass from headword_full
                    headword_full = rom.get('headword_full', '')
                    patterns = {
                        'conjugation': (r'<span class=\\?"conjugation\\?"><acronym title=\\?"([^<][a-z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1)),
                        'verbclass': (r'<span class=\\?"verbclass\\?"><acronym title=\\?"([^<][a-zA-Z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1))
                    }

                    extracted_data = extract_patterns(headword_full, patterns)
                    rom_data.update(extracted_data)
                    rom_data['headword_full'] = extracted_data['text']

                    for arab in rom.get('arabs', []):
                        arab_data = {
                            "header": arab.get("header", ""),
                            "sense": "",
                            "entrynumber": "",
                            "reflection": "",
                            "translations": []
                        }

                        # Extract sense, entrynumber, and reflection from header
                        header = arab.get('header', '')
                        patterns = {
                            'entrynumber': (r'^\d\.', lambda match: match.group(0)),
                            'sense': (r'<span class=\\?"sense\\?">\(?(.*?)\)?</span>', lambda match: match.group(1)),
                            'reflection': (r'<span class=\\?"reflection\\?">\(?(.*?)\)?</span>', lambda match: match.group(1))
                        }

                        extracted_data = extract_patterns(header, patterns)
                        arab_data.update(extracted_data)
                        arab_data['header'] = extracted_data['text']

                        # Filter and add translations
                        for translation in arab.get('translations', []):
                            translation_data = {
                                "source": translation.get("source", ""),
                                "target": translation.get("target", "")
                            }

                            extracted_data = extract_patterns(translation_data['source'], patterns)
                            translation_data.update(extracted_data)
                            translation_data['source'] = extracted_data['text']

                            arab_data['translations'].append(translation_data)

                        rom_data["arabs"].append(arab_data)

                    hit_data["roms"].append(rom_data)
                lang_data["hits"].append(hit_data)

            processed_data.append(lang_data)

        # Save the processed data (optional or for further reconciliation)
        with open(concatenated_file_path.replace('.json', '_processed.json'), 'w', encoding='utf-8') as output_file:
            json.dump(processed_data, output_file, ensure_ascii=False, indent=4)

        print(f"Processing and reconciliation completed. Processed data saved.")

    except Exception as e:
        print(f"An error occurred: {e}")


# Main workflow logic
if mode == "fetch":
    fetch_and_concatenate()
elif mode == "process":
    process_and_reconcile()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process")
