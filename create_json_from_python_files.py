#!/usr/bin/env python3

import os
import re
import json

# Define the directory containing Python files
directory = "/Users/phobrla/Documents/GitHub/PONS-API/Archive"

# Output JSON filename
output_json = "output.json"

# Initialize a list to store file data
file_data = []

# Regex pattern to extract version from filenames
version_pattern = re.compile(r"PONSAPI-(\d+)\.py")

# Process each file in the directory
for filename in os.listdir(directory):
	if filename.endswith(".py"):  # Only process Python files
		match = version_pattern.match(filename)
		if match:  # Check if the filename matches the expected pattern
			version = match.group(1)  # Extract the version number
			file_path = os.path.join(directory, filename)
			with open(file_path, "r") as file:
				content = file.read()  # Read the file content
			# Add the data to the list
			file_data.append({"version": version, "content": content})
		else:
			print(f"Skipping file with unexpected name format: {filename}")
			
# Write the collected data to a JSON file
with open(output_json, "w") as json_file:
	json.dump(file_data, json_file, indent=4)
	
print(f"Data successfully written to {output_json}")