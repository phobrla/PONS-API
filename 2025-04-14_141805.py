#!/usr/bin/env python3

import os
import re
import json
from datetime import datetime
from collections import Counter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from pyxlsb import open_workbook

# Selector to choose the function to run
mode = "reconcile"

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# Paths and directories
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
processed_file_path = os.path.join(base_directory, "processed.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{datetime.now().strftime('%Y%m%dT%H%M%S')}.xlsx")
schematic_file_path = os.path.join(base_directory, "schematic.json")

# Ensure the output directory exists
os.makedirs(base_directory, exist_ok=True)

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Summary data for logging
summary_data = Counter()


def fetch():
    # Fetch data from the concatenated JSON file and save it to a processed format.
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    with open(concatenated_file_path, "r", encoding="utf-8") as file:
        concatenated_data = json.load(file)

    # Save the concatenated data as-is for now into the processed file
    with open(processed_file_path, "w", encoding="utf-8") as processed_file:
        json.dump(concatenated_data, processed_file, ensure_ascii=False, indent=4)


def process():
    # Process the fetched JSON data to extract patterns and perform regex replacements.
    if not os.path.exists(processed_file_path):
        print(f"Processed JSON file not found at {processed_file_path}. Please run 'fetch' mode first.")
        return

    with open(processed_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    processed_data = []

    # Define regex patterns and replacements
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
            continue  # Skip entries with errors

        # Process patterns from the response
        for language_entry in response_data.get("entries", []):
            for hit in language_entry.get("hits", []):
                for rom in hit.get("roms", []):
                    headword_full = rom.get("headword_full", "")
                    extracted_data, processed_text = extract_patterns(headword_full, regex_patterns)
                    rom.update(extracted_data)
                    rom["headword_full_after_regex"] = perform_replacements(processed_text, regex_replacements)

        processed_data.append(entry)

    # Save the processed data back to the processed file
    with open(processed_file_path, "w", encoding="utf-8") as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)


def extract_patterns(text, patterns):
    # Extract data from text using regex patterns.
    extracted_data = {}
    remaining_text = text
    for key, (pattern, func) in patterns.items():
        matches = re.finditer(pattern, remaining_text)
        extracted_matches = [func(match) for match in matches]
        if extracted_matches:
            extracted_data[key] = extracted_matches if len(extracted_matches) > 1 else extracted_matches[0]
            remaining_text = re.sub(pattern, "", remaining_text, count=(1 if len(extracted_matches) == 1 else 0))
    return extracted_data, remaining_text.strip()


def perform_replacements(text, replacements):
    # Perform regex replacements on a string.
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text


def schematize():
    # Generate a schematic representation of the data for analysis.
    if not os.path.exists(processed_file_path):
        print(f"Processed JSON file not found at {processed_file_path}. Please run 'process' mode first.")
        return

    with open(processed_file_path, "r", encoding="utf-8") as file:
        processed_data = json.load(file)

    schematic = {}
    for entry in processed_data:
        query = entry["query"]
        data = entry.get("data", {})
        if "error" not in data:
            schematic[query] = {"entries_count": len(data.get("entries", []))}
        else:
            schematic[query] = {"error": data.get("error")}

    with open(schematic_file_path, "w", encoding="utf-8") as file:
        json.dump(schematic, file, ensure_ascii=False, indent=4)
    print(f"Schematic generated and saved to {schematic_file_path}")


def concatenate():
    # Concatenate all processed JSON data into a single JSON file.
    concatenated_data = []
    for file_name in os.listdir(base_directory):
        if file_name.endswith(".json") and file_name != "concatenated.json":
            file_path = os.path.join(base_directory, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                concatenated_data.extend(json.load(file))

    with open(concatenated_file_path, "w", encoding="utf-8") as file:
        json.dump(concatenated_data, file, ensure_ascii=False, indent=4)
    print(f"Concatenated data saved to {concatenated_file_path}")


def reconcile_entries():
    # Reconcile entries using the processed JSON data and the Anki table.
    if not os.path.exists(processed_file_path):
        print(f"Processed JSON file not found at {processed_file_path}. Please run 'process' mode first.")
        return

    if not os.path.exists(flashcards_xlsb_path):
        print(f"Flashcards.xlsb file not found at {flashcards_xlsb_path}. Please ensure it exists.")
        return

    try:
        with open(processed_file_path, 'r', encoding='utf-8') as file:
            processed_data = json.load(file)
        
        anki_data = load_anki_table_from_xlsb(flashcards_xlsb_path)

        # Create mappings for Anki table
        query_to_pos = {}
        query_to_note_id = {}
        for row in anki_data:
            bulgarian_1 = row.get("Bulgarian 1", "").strip() if row.get("Bulgarian 1") else ""
            bulgarian_2 = row.get("Bulgarian 2", "").strip() if row.get("Bulgarian 2") else ""
            part_of_speech = row.get("Part of Speech", "").strip() if row.get("Part of Speech") else ""
            note_id = row.get("Note ID", "").strip() if row.get("Note ID") else ""

            if bulgarian_1:
                query_to_pos[bulgarian_1] = part_of_speech
                query_to_note_id[bulgarian_1] = note_id
            if bulgarian_2:
                query_to_pos[bulgarian_2] = part_of_speech
                query_to_note_id[bulgarian_2] = note_id

        # Reconciliation logic
        results = []
        for entry in processed_data:
            query = entry["query"]

            # Default values for fields
            original_part_of_speech = query_to_pos.get(query, "Unknown")
            original_note_id = query_to_note_id.get(query, "")
            revised_query = None
            revised_note_id = ""
            revised_part_of_speech = ""
            revised_status = ""
            revised_result = ""

            # Logic for revised query
            if original_part_of_speech == "Verb":
                for cutoff in cutoff_strings:
                    if query.endswith(cutoff):
                        revised_query = query[:-len(cutoff)].strip()
                        break

            if revised_query:
                revised_note_id = query_to_note_id.get(revised_query, "")
                revised_part_of_speech = query_to_pos.get(revised_query, "Unknown")
                revised_status = "Success" if revised_note_id else "Failure"
                revised_result = "Match Found" if revised_note_id else "No Match"

            results.append([
                original_note_id, query, original_part_of_speech, 
                revised_query, revised_part_of_speech, revised_status, revised_result, revised_note_id
            ])

        # Export results to Excel
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Reconciliation"

        # Write headers
        headers = [
            "Original Note ID", "Original Query", "Original Part of Speech",
            "Revised Query", "Revised Part of Speech", "Revised Status",
            "Revised Result", "Revised Note ID"
        ]
        sheet.append(headers)

        # Write rows
        for row in results:
            sheet.append(row)

        workbook.save(xlsx_output_file)
        print(f"Reconciliation completed. Results saved to {xlsx_output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Main workflow
if mode == "fetch":
    fetch()
elif mode == "process":
    process()
elif mode == "schematize":
    schematize()
elif mode == "concatenate":
    concatenate()
elif mode == "reconcile":
    reconcile_entries()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, schematize, concatenate, reconcile")