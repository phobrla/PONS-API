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
flashcards_xlsb_path = os.path.join(base_directory, "Flashcards.xlsb")

# Generate the timestamp suffix
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
xlsx_output_file = os.path.join(base_directory, f"reconciliation_results_{timestamp}.xlsx")

# Ensure the output directory exists
os.makedirs(base_directory, exist_ok=True)

# Strings to be cut off during the re-search
cutoff_strings = [
    " се", " [в]", " си", " [с]", " за", " в", " (се)", " (се) [с]", " (се) да"
]

# Summary data for logging
summary_data = Counter()


def load_anki_table_from_xlsb(file_path):
    """
    Load the 'Anki' table from the Flashcards.xlsb file in read-only mode.
    This function can parse the file even if it is open in Microsoft Excel.
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
        print(f"An error occurred while reading the 'Anki' table: {e}")
    
    return anki_data


def reconcile_entries():
    # Load required files
    if not os.path.exists(concatenated_file_path):
        print(f"Concatenated JSON file not found at {concatenated_file_path}. Please run 'concatenate' mode first.")
        return

    if not wos.path.exists(flashcards_xlsb_path):
        print(f"Flashcards.xlsb file not found at {flashcards_xlsb_path}. Please ensure it exists.")
        return

    try:
        # Load concatenated data
        with open(concatenated_file_path, 'r', encoding='utf-8') as file:
            concatenated_data = json.load(file)
            concatenated_queries = set(entry["query"] for entry in concatenated_data)
        
        # Load the "Anki" table from Flashcards.xlsb
        anki_data = load_anki_table_from_xlsb(flashcards_xlsb_path)

        # Create a mapping of queries to parts of speech and Note IDs
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

        # Process data
        results = []
        unmatched_revised_queries = []  # Collect unmatched revised queries for debugging

        for entry in concatenated_data:
            query = entry["query"]

            # Default values for fields
            revised_query = ""
            cutoff_type = ""
            cutoff_applied = ""
            found_in_concatenated = "Neither"
            found_in_pos = "Neither"
            revised_status = ""
            revised_result = ""
            revised_part_of_speech = ""
            original_note_id = ""
            revised_note_id = ""

            # Part of Speech
            original_part_of_speech = query_to_pos.get(query, "Unknown")
            original_note_id = query_to_note_id.get(query, "")

            # Handle Verbs with cutoff logic
            if original_part_of_speech == "Verb":
                for cutoff in cutoff_strings:
                    if query.endswith(cutoff):
                        revised_query = query[: -len(cutoff)].strip()
                        cutoff_type = "Verb Cutoff"
                        cutoff_applied = cutoff
                        break

            # Handle Adverbs and Unclassified Words
            elif original_part_of_speech in ["Adverb", "Unclassified Word"]:
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

            # Determine "Found in" values for original and revised queries
            original_found_in_concatenated = query in concatenated_queries
            revised_found_in_concatenated = revised_query in concatenated_queries if revised_query else False
            original_found_in_pos = query in query_to_pos
            revised_found_in_pos = revised_query in query_to_pos if revised_query else False

            # Consolidate "Found in Concatenated"
            if original_found_in_concatenated and revised_found_in_concatenated:
                found_in_concatenated = "Both"
            elif original_found_in_concatenated:
                found_in_concatenated = "Original"
            elif revised_found_in_concatenated:
                found_in_concatenated = "Revised"

            # Consolidate "Found in POS"
            if original_found_in_pos and revised_found_in_pos:
                found_in_pos = "Both"
            elif original_found_in_pos:
                found_in_pos = "Original"
            elif revised_found_in_pos:
                found_in_pos = "Revised"

            # Validate Revised Query
            if revised_query:
                revised_part_of_speech = query_to_pos.get(revised_query, "Unknown")
                revised_note_id = query_to_note_id.get(revised_query, "")
                revised_status = "Success" if revised_found_in_concatenated else "Failure"
                revised_result = "Match Found" if revised_found_in_pos else "No Match"

                # Log unmatched revised queries
                if not revised_found_in_concatenated:
                    unmatched_revised_queries.append(revised_query)
            else:
                # Ensure blanks for revised fields if revised query is blank
                revised_status = ""
                revised_result = ""

            results.append([
                query, original_part_of_speech, revised_query, revised_part_of_speech, cutoff_type, cutoff_applied,
                revised_status, revised_result, found_in_concatenated, found_in_pos, original_note_id, revised_note_id
            ])

        # Create the Excel file only after all processing is complete
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Sheet1"

        # Write headers
        headers = [
            "Original Query", "Original Part of Speech", "Revised Query", "Revised Part of Speech",
            "Cutoff Type", "Cutoff Applied", "Revised Status", "Revised Result",
            "Found in Concatenated", "Found in POS", "Original Note ID", "Revised Note ID"
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
        table_range = f"A1:L{sheet.max_row}"
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

    except Exception as e:
        print(f"An error occurred: {e}. Check the log for details.")

# Main workflow
if mode == "reconcile":
    reconcile_entries()
else:
    print(f"Unknown mode: {mode}")
    print("Available modes: reconcile")