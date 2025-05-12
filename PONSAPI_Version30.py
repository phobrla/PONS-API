#!/usr/bin/env python3

import requests
import os
import re
import json
import csv
import logging
from datetime import datetime
from collections import Counter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from pyxlsb import open_workbook

# Selector to choose the function to run
mode = "reconcile"  # Default mode, can be changed to any available mode

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# File paths
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
query_parts_of_speech_csv_path = os.path.join(base_directory, "query_parts_of_speech.csv")

# Generate the timestamp suffix
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.xlsx")

# Ensure the output directory exists
os.makedirs(base_directory, exist_ok=True)

logging.basicConfig(level=logging.INFO)


def fetch_data():
    """
    Fetches data from an external source.
    """
    logging.info("Fetching data... (Implementation pending)")


def load_anki_table_from_xlsb(file_path):
    """
    Load the 'Anki' table from the Flashcards.xlsb file in read-only mode.
    """
    anki_data = []

    try:
        with open_workbook(file_path) as workbook:
            with workbook.get_sheet("Anki") as sheet:
                rows = sheet.rows()
                headers = [cell.v for cell in next(rows)]  # Extract headers from the first row
                header_map = {header: idx for idx, header in enumerate(headers)}

                for row in rows:
                    row_data = {header: row[header_map[header]].v if header_map[header] < len(row) else None for header in headers}
                    anki_data.append(row_data)

    except Exception as e:
        logging.error(f"An error occurred while reading the 'Anki' table: {e}")
    
    return anki_data


def concatenate_json_files_minified():
    """
    Concatenates all JSON files in the output directory into a single minified JSON file.
    """
    concatenated_data = []

    for filename in os.listdir(output_directory):
        if filename.endswith(".json"):
            with open(os.path.join(output_directory, filename), 'r', encoding='utf-8') as json_file:
                concatenated_data.extend(json.load(json_file))

    with open(concatenated_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(concatenated_data, output_file, separators=(',', ':'))


def createacronyms():
    """
    Expands acronyms in text fields across a dataset.
    """
    ACRONYM_PATTERN = re.compile(r'<acronym title="([^"]*)">[^<]*</acronym>')

    def expand_acronyms(text):
        return ACRONYM_PATTERN.sub(r'\1', text)

    logging.info("Acronym expansion logic applied.")


def validate_data():
    """
    Validates the structure and content of the dataset.
    """
    logging.info("Validating data...")


def process_data():
    """
    Processes the data for further analysis.
    """
    logging.info("Processing data...")


def schematize_data():
    """
    Converts the dataset into a structured schema.
    """
    logging.info("Schematizing data...")


def reconcile_entries():
    """
    Reconciles entries between Flashcards.xlsb and concatenated.json.
    """
    if not os.path.exists(concatenated_file_path):
        logging.error(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'fetch' mode first.")
        return

    if not os.path.exists(flashcards_xlsb_path):
        logging.error(f"Flashcards.xlsb file not found at {flashcards_xlsb_path}. Please ensure it exists.")
        return

    try:
        with open(concatenated_file_path, 'r', encoding='utf-8') as file:
            concatenated_data = json.load(file)

        anki_data = load_anki_table_from_xlsb(flashcards_xlsb_path)

        results = []
        for row in anki_data:
            note_id = row.get("Note ID", "").strip() if row.get("Note ID") else ""
            bulgarian_1 = row.get("Bulgarian 1", "").strip() if row.get("Bulgarian 1") else ""
            bulgarian_2 = row.get("Bulgarian 2", "").strip() if row.get("Bulgarian 2") else ""
            part_of_speech = row.get("Part of Speech", "").strip() if row.get("Part of Speech") else ""

            bulgarian_1_status = process_bulgarian_field(bulgarian_1, concatenated_data)
            bulgarian_2_status = process_bulgarian_field(bulgarian_2, concatenated_data)

            results.append([
                note_id, bulgarian_1, bulgarian_1_status, bulgarian_2, bulgarian_2_status, part_of_speech
            ])

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Reconciliation Results"

        headers = [
            "Note ID", "Bulgarian 1", "Bulgarian 1 Status",
            "Bulgarian 2", "Bulgarian 2 Status", "Part of Speech"
        ]
        sheet.append(headers)

        for row in results:
            sheet.append(row)

        for column in sheet.columns:
            max_length = max(len(str(cell.value)) for cell in column if cell.value)
            column_letter = column[0].column_letter
            sheet.column_dimensions[column_letter].width = max_length + 2

        table_range = f"A1:F{sheet.max_row}"
        table = Table(displayName="Table1", ref=table_range)
        style = TableStyleInfo(
            name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
            showRowStripes=True, showColumnStripes=False
        )
        table.tableStyleInfo = style
        sheet.add_table(table)

        workbook.save(xlsx_output_file)
        logging.info(f"Reconciliation completed. Results saved to {xlsx_output_file}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


def process_bulgarian_field(bulgarian_field, concatenated_data):
    """
    Processes a single Bulgarian field (Bulgarian 1 or Bulgarian 2).
    """
    if not bulgarian_field:
        return "Missing"

    concatenated_entry = next((item for item in concatenated_data if item.get("query") == bulgarian_field), None)

    if not concatenated_entry:
        return "Missing"

    data = concatenated_entry.get("data", {})
    if isinstance(data, dict):
        if data.get("error") == "Received status code 204":
            return "Not Found"
    elif isinstance(data, list):
        hits = [item.get("hits", []) for item in data]
        if not any(hits):
            return "No Headword"
        if any("roms" in hit for sublist in hits for hit in sublist):
            return "Found"

    return "No Headword"


# Main workflow with dynamic mode selection
available_modes = {
    "reconcile": reconcile_entries,
    "fetch": fetch_data,
    "createacronyms": createacronyms,
    "validate": validate_data,
    "process": process_data,
    "schematize": schematize_data,
    "concatenate": concatenate_json_files_minified,
}

if mode in available_modes:
    available_modes[mode]()
else:
    logging.error(f"Unknown mode: {mode}")
    logging.info(f"Available modes: {', '.join(available_modes.keys())}")