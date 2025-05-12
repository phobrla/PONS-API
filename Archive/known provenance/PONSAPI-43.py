#!/usr/bin/env python3

import requests
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
schema_file_path = os.path.join(base_directory, "schema.json")
query_parts_of_speech_json_path = os.path.join(base_directory, "Query Parts of Speech.json")

# Generate the timestamp suffix
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.xlsx")
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
logging.info(f"XLSX Output File: {xlsx_output_file}")
logging.info(f"Log File: {log_file_path}")

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Summary data for logging
summary_data = Counter()

# Function to reconcile specific cases in the concatenated JSON
def reconcile_entries():
    logging.info("Starting reconcile mode.")
    
    # Verify the existence of required files
    if not os.path.exists(concatenated_file_path):
        logging.error(f"Concatenated JSON file not found at: {concatenated_file_path}")
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    if not os.path.exists(query_parts_of_speech_json_path):
        logging.error(f"Query Parts of Speech JSON file not found at: {query_parts_of_speech_json_path}")
        print(f"Query Parts of Speech JSON file not found at {query_parts_of_speech_json_path}. Please ensure it exists.")
        return

    # Load the concatenated JSON data
    try:
        with open(concatenated_file_path, 'r', encoding='utf-8') as file:
            concatenated_data = json.load(file)
            concatenated_queries = set(entry["query"] for entry in concatenated_data)
        logging.debug(f"Total queries in concatenated.json: {len(concatenated_data)}")
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Error reading concatenated file '{concatenated_file_path}': {e}")
        return

    # Load the Query Parts of Speech JSON file
    bulgarian_to_pos = {}
    try:
        with open(query_parts_of_speech_json_path, 'r', encoding='utf-8') as file:
            parts_of_speech_data = json.load(file).get("JSONdata", [])
            for entry in parts_of_speech_data:
                bulgarian_word = entry.get("Bulgarian", "").strip()
                part_of_speech = entry.get("Part of Speech", "").strip()
                if bulgarian_word and part_of_speech:
                    bulgarian_to_pos[bulgarian_word] = part_of_speech
        logging.debug(f"Total mappings in Query Parts of Speech.json: {len(bulgarian_to_pos)}")
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Error reading JSON file '{query_parts_of_speech_json_path}': {e}")
        return

    # Create a new Excel workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"  # Set the sheet title to "Sheet1"

    # Write the headers
    headers = [
        "Original Query", "Revised Query", "Original Part of Speech", "Cutoff Type",
        "Cutoff Applied", "Original Status", "Revised Status", "Revised Result",
        "Found in concatenated", "Found in POS"
    ]
    sheet.append(headers)

    # Iterate over the concatenated data to find entries matching the criteria
    for entry in concatenated_data:
        query = entry["query"]
        original_data = entry.get("data", None)

        # Default values for fields
        revised_query = ""
        cutoff_type = ""
        cutoff_applied = ""
        revised_status = ""
        revised_result = ""

        # Part of Speech
        original_part_of_speech = bulgarian_to_pos.get(query, "Unknown")
        if original_part_of_speech == "Unknown":
            logging.warning(f"Part of Speech for query '{query}' is unknown.")
            summary_data[f"Unknown Part of Speech: {query}"] += 1

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

        # Determine "Found in" values
        found_in_concatenated = (
            "Original" if query in concatenated_queries else
            "Revised" if revised_query in concatenated_queries else
            "Neither"
        )
        found_in_pos = (
            "Original" if query in bulgarian_to_pos else
            "Revised" if revised_query in bulgarian_to_pos else
            "Neither"
        )

        # Leave "Revised Status" and "Revised Result" blank if "Found in POS" equals "Original"
        if found_in_pos == "Original":
            revised_status = ""
            revised_result = ""

        # Append the row to the worksheet
        sheet.append([
            query, revised_query, original_part_of_speech,
            cutoff_type, cutoff_applied, "Processed", revised_status, revised_result,
            found_in_concatenated, found_in_pos
        ])

    # Auto-fit column widths based on header length and content
    for column in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in column if cell.value)
        column_letter = column[0].column_letter  # Get the column letter
        sheet.column_dimensions[column_letter].width = max_length + 2  # Add padding for readability

    # Create a table in the worksheet
    table_range = f"A1:J{sheet.max_row}"  # Covers all rows including headers
    table = Table(displayName="Table1", ref=table_range)

    # Apply a table style without banded columns
    style = TableStyleInfo(
        name="TableStyleMedium2",  # Dark Teal, Table Style Medium 2
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,  # Keep row stripes
        showColumnStripes=False  # Turn off banded columns
    )
    table.tableStyleInfo = style
    sheet.add_table(table)

    # Save the workbook to an XLSX file
    try:
        workbook.save(xlsx_output_file)
        logging.info(f"Reconciliation completed. Results saved to {xlsx_output_file}")
        print(f"Reconciliation completed. Results saved to {xlsx_output_file}")
    except IOError as e:
        logging.error(f"Error writing reconciliation results to '{xlsx_output_file}': {e}")

    # Generate and log summary
    logging.info("\n--- Summary ---")
    for key, count in summary_data.items():
        logging.info(f"{key}: {count}")

# Main workflow
if mode == "reconcile":
    reconcile_entries()
else:
    logging.error(f"Unknown mode: {mode}")
    print(f"Unknown mode: {mode}")
    print("Available modes: reconcile")