# Function to concatenate all JSON files into a single minified JSON file
def concatenate_json_files_minified():
    concatenated_data = []

    for filename in os.listdir(output_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(output_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # Add the filename (minus .json) as a top-level field
                data_with_query = {
                    "query": filename[:-5],  # Remove ".json"
                    "data": data
                }
                concatenated_data.append(data_with_query)

    # Write the concatenated data to a single minified JSON file
    with open(concatenated_file_path, 'w', encoding='utf-8') as out_file:
        json.dump(concatenated_data, out_file, ensure_ascii=False, separators=(',', ':'))

    print(f"Minified concatenated JSON data saved to {concatenated_file_path}")