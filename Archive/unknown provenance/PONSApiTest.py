import requests  # Import the requests library for making HTTP requests
import json  # Import the json library for handling JSON data
import re  # Import the re library for regular expressions

# Toggle to control whether to return the raw API response
return_raw_api_response = True

# Array for the queries
query_terms = ["искам", "харесвам"]

# Function to extract patterns from the text
def extract_patterns(text, patterns):
    extracted_data = {}
    remaining_text = text
    for key, (pattern, func) in patterns.items():
        matches = re.finditer(pattern, remaining_text)
        extracted_matches = [func(match) for match in matches]
        if extracted_matches:
            extracted_data[key] = extracted_matches if len(extracted_matches) > 1 else extracted_matches[0]
            remaining_text = re.sub(pattern, '', remaining_text, count=(1 if len(extracted_matches) == 1 else 0))
    return extracted_data, remaining_text.strip()

# Function to fetch dictionary data
def fetch_dictionary_data(term):
    url = f"https://api.pons.com/v1/dictionary?q={term}&l=bgen"  # Define the URL for the API request
    headers = {
        "X-Secret": "XXX"  # Define the headers with the secret key
    }
    response = requests.get(url, headers=headers)  # Make a GET request to the API with the headers

    if return_raw_api_response:
        if response.status_code == 200:
            print(json.dumps(response.json(), ensure_ascii=False, indent=4))
        else:
            print(f"Error: Received status code {response.status_code}")
        return

    if response.status_code == 200:  # Check if the response status code is 200 (OK)
        response_json = response.json()  # Parse the response JSON

        # Dictionary for regex patterns
        regex_patterns = {
            'conjugation1': r'<span class="conjugation"><acronym title="([^"]+)">[^<]*</acronym></span>',  # Updated to match the first instance
            'conjugation2': r', <span class="headword">[^<]+</span> <span class="conjugation"><acronym title="([^"]+)">[^<]+</acronym></span>',
            'word_class': r'<span class="wordclass">([^<]+)</span>',
            'verb_class': r'<span class="verbclass"><acronym title="([^"]+)">[^<]+</acronym></span>',
            'headword': r'<strong class="headword">([^<]+)</strong>'
        }

        # Dictionary for regex replacements
        regex_replacements = {
            r'<acronym title=\\?"([^<].*)\\?">[^<].*</acronym>': r'\1',  # Define regex pattern to replace <acronym> tags with their title attribute values
            r'<strong class=\\?"headword\\?">([^<]+)</strong>': r'\1',  # Define regex pattern to remove <strong class="headword"> tags, leaving only the text
            r'<strong class=\\?"tilde\\?">([^<]+)</strong>': r'\1'  # Define regex pattern to remove <strong class="tilde"> tags, leaving only the text
        }

        # Function to perform regex replacements on a string
        def perform_replacements(text):
            for pattern, replacement in regex_replacements.items():
                text = re.sub(pattern, replacement, text)
            return text

        # Filter out entries with <span class="example"> and sources other than <strong class="headword"></strong>
        for language_entry in response_json:  # Loop through each language entry in the response
            for hit in language_entry.get('hits', []):  # Loop through each hit in the language entry
                for level_one in hit.get('roms', []):  # Loop through each level one in the hit
                    # Extract conjugation information
                    conjugation_match = re.search(regex_patterns['conjugation1'], level_one.get('headword_full', ''))  # Search for the regex pattern in the 'headword_full' field
                    if conjugation_match:  # Check if there is a match
                        conjugation = conjugation_match.group(1)  # Extract the conjugation from the match
                        level_one['conjugation1'] = conjugation  # Add the conjugation to the level one dictionary

                    conjugation2_match = re.search(regex_patterns['conjugation2'], level_one.get('headword_full', ''))
                    if conjugation2_match:
                        conjugation2 = conjugation2_match.group(1)
                        level_one['conjugation2'] = conjugation2

                    verb_class_match = re.search(regex_patterns['verb_class'], level_one.get('headword_full', ''))
                    if verb_class_match:
                        verb_class = verb_class_match.group(1)
                        level_one['verb_class'] = verb_class

                    for level_two in level_one.get('arabs', []):  # Loop through each level two in the level one
                        level_two['translations'] = [
                            translation for translation in level_two.get('translations', [])  # Filter translations
                            if re.match(regex_patterns['headword'], translation['source'])  # Include those with <strong class="headword">
                        ]

                    # Perform regex replacements on relevant fields
                    level_one['headword_full'] = perform_replacements(level_one.get('headword_full', ''))
                    for level_two in level_one.get('arabs', []):
                        level_two['header'] = perform_replacements(level_two.get('header', ''))
                        for translation in level_two.get('translations', []):
                            translation['source'] = perform_replacements(translation.get('source', ''))

        # Additional functionality to extract patterns and aggregate data
        aggregated_data = []

        for language_entry in response_json:  # Iterate over each language entry in the JSON response
            language_data = {
                "language": language_entry.get("lang", ""),
                "hits": []
            }

            for hit in language_entry.get('hits', []):  # Iterate over each hit in the language entry
                hit_data = {
                    "type": hit.get("type", ""),
                    "open_dict": hit.get("opendict", False),
                    "level_one": []
                }

                for level_one in hit.get('roms', []):  # Iterate over each level one in the hit
                    level_one_data = {
                        "headword1": level_one.get("headword", ""),
                        "headword2": "",
                        "headword_full": level_one.get("headword_full", ""),
                        "headword_full_after_regex": "",
                        "word_class": "",
                        "conjugation1": "",
                        "conjugation2": "",
                        "verb_class": "",
                        "level_two": []
                    }

                    # Extract conjugation and verb_class from headword_full
                    headword_full = level_one.get('headword_full', '')
                    patterns = {
                        'conjugation1': (r'<span class=\\?"conjugation\\?"><acronym title=\\?"([^<][a-z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1)),
                        'conjugation2': (r', <span class=\\?"headword\\?">([^<]+)</span> <span class=\\?"conjugation\\?"><acronym title=\\?"([^<][a-z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1)),
                        'word_class': (r'<span class=\\?"wordclass\\?">([^<][a-zA-Z ]+)</span>', lambda match: match.group(1)),
                        'verb_class': (r'<span class=\\?"verbclass\\?"><acronym title=\\?"([^<][a-zA-Z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1)),
                        'headword1': (r'^(.*?) <span class=\\?"conjugation\\?">', lambda match: match.group(1)),
                        'headword2': (r'<span class=\\?"headword\\?">([^<]+)</span>', lambda match: match.group(1))
                    }

                    extracted_data, processed_text = extract_patterns(headword_full, patterns)
                    level_one_data.update(extracted_data)
                    level_one_data['headword_full_after_regex'] = perform_replacements(processed_text)

                    for level_two in level_one.get('arabs', []):  # Iterate over each level two in the level one
                        level_two_data = {
                            "header": level_two.get("header", ""),
                            "sense": "",
                            "entry_number": "",
                            "reflection": "",
                            "translations": []
                        }

                        # Extract sense, entry_number, and reflection from header
                        header = level_two.get('header', '')
                        patterns = {
                            'entry_number': (r'^\d\.', lambda match: match.group(0)),
                            'sense': (r'<span class=\\?"sense\\?">\(?(.*?)\)?</span>', lambda match: match.group(1)),
                            'reflection': (r'<span class=\\?"reflection\\?">\(?(.*?)\)?</span>', lambda match: match.group(1))
                        }

                        extracted_data, processed_text = extract_patterns(header, patterns)
                        level_two_data.update(extracted_data)
                        level_two_data['header'] = processed_text

                        # Filter and add translations
                        for translation in level_two.get('translations', []):
                            translation_data = {
                                "source": translation.get("source", ""),
                                "target": translation.get("target", "")
                            }

                            extracted_data, processed_text = extract_patterns(translation_data['source'], patterns)
                            translation_data.update(extracted_data)
                            translation_data['source'] = processed_text

                            level_two_data['translations'].append(translation_data)

                        level_one_data["level_two"].append(level_two_data)

                hit_data["level_one"].append(level_one_data)
            language_data["hits"].append(hit_data)
        aggregated_data.append(language_data)

        # Print the aggregated data in JSON format
        print(json.dumps(aggregated_data, ensure_ascii=False, indent=4))
        
    else:
        print(f"Error: Received status code {response.status_code}")

if __name__ == "__main__":
    for term in query_terms:
        fetch_dictionary_data(term)  # Call the function for each query term