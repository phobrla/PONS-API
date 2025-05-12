#!/usr/bin/env python3

import os
import json
import re
import csv
import logging
import requests
from datetime import datetime
from collections import Counter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from pyxlsb import open_workbook

# Selector to choose the function to run
# Options: "fetch", "process", "concatenate", "schematize", "reconcile"
mode = "reconcile"

# Base directory for all file paths
base_directory = "/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning"

# Paths and directories
input_file_path = os.path.join(base_directory, "Inputs_for_PONS_API.txt")
output_directory = os.path.join(base_directory, "PONS json Files")
concatenated_file_path = os.path.join(base_directory, "concatenated.json")
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")
csv_output_file = os.path.join(base_directory, "reconciliation_results.csv")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{datetime.now().strftime('%Y%m%dT%H%M%S')}.xlsx")

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Summary data for logging
summary_data = Counter()

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Set up logging
logging.basicConfig(
    filename=os.path.join(output_directory, "PONSAPI.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to load the 'Anki' table from Flashcards.xlsb
def load_anki_table_from_xlsb(file_path):
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

# Function to fetch data from the API
def fetch_and_save(term, output_file_path):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"
    headers = {"X-Secret": "XXX"}
    response = requests.get(url, headers=headers)
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        if response.status_code == 200:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
        else:
            json.dump({"error": f"Received status code {response.status_code}", "response_text": response.text}, json_file, ensure_ascii=False, indent=4)

# Function to process a single Bulgarian field
def process_bulgarian_field(bulgarian_field, concatenated_data):
    if not bulgarian_field:
        return "Missing"
    concatenated_entry = next((item for item in concatenated_data if item.get("query") == bulgarian_field), None)
    if not concatenated_entry:
        return "Missing"
    data = concatenated_entry.get("data", {})
    if isinstance(data, dict) and data.get("error") == "Received status code 204":
        return "Not Found"
    elif isinstance(data, list) and not any(hit.get("hits", []) for hit in data):
        return "No Headword"
    return "Found"

# Function to reconcile entries
def reconcile_entries():
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
            note_id = row.get("Note ID", "").strip()
            bulgarian_1 = row.get("Bulgarian 1", "").strip()
            bulgarian_2 = row.get("Bulgarian 2", "").strip()
            part_of_speech = row.get("Part of Speech", "").strip()
            bulgarian_1_status = process_bulgarian_field(bulgarian_1, concatenated_data)
            bulgarian_2_status = process_bulgarian_field(bulgarian_2, concatenated_data)
            results.append([note_id, bulgarian_1, bulgarian_1_status, bulgarian_2, bulgarian_2_status, part_of_speech])
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Reconciliation Results"
        headers = ["Note ID", "Bulgarian 1", "Bulgarian 1 Status", "Bulgarian 2", "Bulgarian 2 Status", "Part of Speech"]
        sheet.append(headers)
        for row in results:
            sheet.append(row)
        for column in sheet.columns:
            max_length = max(len(str(cell.value)) for cell in column if cell.value)
            column_letter = column[0].column_letter
            sheet.column_dimensions[column_letter].width = max_length + 2
        table = Table(displayName="Table1", ref=f"A1:F{sheet.max_row}")
        style = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
        table.tableStyleInfo = style
        sheet.add_table(table)
        workbook.save(xlsx_output_file)
        logging.info(f"Reconciliation completed. Results saved to {xlsx_output_file}")
    except Exception as e:
        logging.error(f"An error occurred during reconciliation: {e}")

# Main workflow
if mode == "fetch":
    fetch_and_save("example_term", os.path.join(output_directory, "example.json"))
elif mode == "reconcile":
    reconcile_entries()
else:
    logging.warning(f"Unknown mode: {mode}")
    print("Available modes: fetch, process, concatenate, schematize, reconcile")