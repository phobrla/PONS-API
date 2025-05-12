import json
import os
import re

# Directory containing the JSON files
json_files_directory = '/Users/phobrla/Library/CloudStorage/OneDrive-Personal/Documents/Bulgarian Language Learning/PONS json Files'

# Function to extract and process data from a JSON file
def process_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

        # Check for errors in the JSON file
        if "error" in data:
            print(f"Error in file {file_path}: {data['error']}")
            return
        
        # Example processing logic
        # Extract headwords and translations from the JSON
        processed_data = []
        for language_entry in data:
            for hit in language_entry.get('hits', []):
                for rom in hit.get('roms', []):
                    headword = rom.get('headword', 'Unknown')
                    translations = [
                        translation.get('target', 'Unknown')
                        for arab in rom.get('arabs', [])
                        for translation in arab.get('translations', [])
                    ]
                    processed_data.append({
                        "headword": headword,
                        "translations": translations
                    })
        
        # Print the processed data
        print(json.dumps(processed_data, ensure_ascii=False, indent=4))

# Iterate over all JSON files in the directory and process them
for filename in os.listdir(json_files_directory):
    if filename.endswith('.json'):
        process_json_file(os.path.join(json_files_directory, filename))
