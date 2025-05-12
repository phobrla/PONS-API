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
query_parts_of_speech_json_path = os.path.join(base_directory, "Query Parts of Speech.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{datetime.now().strftime('%Y%m%dT%H%M%S')}.xlsx")

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


def setup_logging():
    """
    Sets up the logging configuration and ensures the output directory exists.
    """
    os.makedirs(output_directory, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(base_directory, f"debug_{datetime.now().strftime('%Y%m%dT%H%M%S')}.log"),
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def handle_cutoffs(query, part_of_speech):
    """
    Handles cutoff logic for verbs, adverbs, and unclassified words.

    Args:
        query (str): The original query.
        part_of_speech (str): The part of speech of the query.

    Returns:
        tuple: Revised query, cutoff type, and cutoff applied.
    """
    revised_query = ""
    cutoff_type = ""
    cutoff_applied = ""

    if part_of_speech == "Verb":
        for cutoff in cutoff_strings:
            if query.endswith(cutoff):
                revised_query = query[: -len(cutoff)].strip()
                cutoff_type = "Verb Cutoff"
                cutoff_applied = cutoff
                break
    elif part_of_speech in ["Adverb", "Unclassified Word"]:
        if query.endswith("ено"):
            revised_query = re.sub(r"ено$", "ен", query)
            cutoff_type = "Adverb Modification"
            cutoff_applied = "ено → ен"
        elif query.endswith("но"):
            revised_query = re.sub(r"но$", "ен", query)
            cutoff_type = "Adverb Modification"
            cutoff_applied = "но → ен"
        elif query.endswith("о"):
            revised_query = re.sub(r"о$", "ен", query)
            cutoff_type = "Adverb Modification"
            cutoff_applied = "о → ен"

    return revised_query, cutoff_type, cutoff_applied


def reconcile_entries():
    """
    Reconciles entries between Flashcards.xlsb and concatenated.json.
    Processes 'Bulgarian 1' and 'Bulgarian 2' independently.
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

        # Load the "Anki" table from Flashcards.xlsb
        anki_data = load_anki_table_from_xlsb(flashcards_xlsb_path)

        # Prepare reconciliation results
        results = []

        for row in anki_data:
            note_id = row.get("Note ID", "").strip() if row.get("Note ID") else ""
            bulgarian_1 = row.get("Bulgarian 1", "").strip() if row.get("Bulgarian 1") else ""
            bulgarian_2 = row.get("Bulgarian 2", "").strip() if row.get("Bulgarian 2") else ""
            part_of_speech = row.get("Part of Speech", "").strip() if row.get("Part of Speech") else ""

            # Process Bulgarian 1
            bulgarian_1_status = process_bulgarian_field(bulgarian_1, concatenated_data)

            # Process Bulgarian 2
            bulgarian_2_status = process_bulgarian_field(bulgarian_2, concatenated_data)

            # Append results
            results.append([
                note_id, bulgarian_1, bulgarian_1_status, bulgarian_2, bulgarian_2_status, part_of_speech
            ])

        # Finalize and save results
        save_reconciliation_results(results)

    except Exception as e:
        print(f"An error occurred: {e}")


def process_bulgarian_field(bulgarian_field, concatenated_data):
    """
    Processes a single Bulgarian field (Bulgarian 1 or Bulgarian 2).
    Checks its presence and status in concatenated.json.
    """
    if not bulgarian_field:
        return "Missing"

    # Search for the query in concatenated.json
    concatenated_entry = next((item for item in concatenated_data if item.get("query") == bulgarian_field), None)

    if not concatenated_entry:
        return "Missing"

    # Check the contents of the data field
    data = concatenated_entry.get("data", {})
    if isinstance(data, dict):
        if data.get("error") == "Received status code 204":
            return "Not Found"
    elif isinstance(data, list):
        hits = [item.get("hits", []) for item in data]
        if not any(hits):  # No hits at all
            return "No Headword"
        if any("roms" in hit for sublist in hits for hit in sublist):
            return "Found"

    return "No Headword"


def save_reconciliation_results(results):
    """
    Saves reconciliation results to an Excel file.

    Args:
        results (list): The reconciliation results.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reconciliation Results"

    # Write headers
    headers = [
        "Note ID", "Bulgarian 1", "Bulgarian 1 Status",
        "Bulgarian 2", "Bulgarian 2 Status", "Part of Speech"
    ]
    sheet.append(headers)

    # Write data
    for row in results:
        sheet.append(row)

    # Auto-fit column widths
    for column in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in column if cell.value)
        column_letter = column[0].column_letter
        sheet.column_dimensions[column_letter].width = max_length + 2

    # Apply table style
    table_range = f"A1:F{sheet.max_row}"
    table = Table(displayName="Table1", ref=table_range)
    style = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
        showRowStripes=True, showColumnStripes=False
    )
    table.tableStyleInfo = style
    sheet.add_table(table)

    # Save the workbook
    try:
        workbook.save(xlsx_output_file)
        print(f"Reconciliation completed. Results saved to {xlsx_output_file}")
    except IOError as e:
        print(f"Error writing reconciliation results to '{xlsx_output_file}': {e}")


# Main workflow logic
if mode == "reconcile":
    reconcile_entries()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, reconcile")
