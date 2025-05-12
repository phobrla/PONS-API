rewrite the following python script to use powershell:

import requests
import json
import re

# Toggle to control whether to return the raw API response
RETURN_RAW_API_RESPONSE = False

def extract_patterns(text, patterns):
    result = {}
    for key, (pattern, func) in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = func(match)
            text = re.sub(pattern, '', text)
    result['text'] = text.strip()
    return result

def run_curl_command():
    url = "https://api.pons.com/v1/dictionary?l=bgen&q=искам"
    headers = {
        "X-Secret": "XXX"
    }
    response = requests.get(url, headers=headers)
    
    if RETURN_RAW_API_RESPONSE:
        if response.status_code == 200:
            print(json.dumps(response.json(), ensure_ascii=False, indent=4))
        else:
            print(f"Error: Received status code {response.status_code}")
        return

    if response.status_code == 200:  # Check if the response status code is 200 (OK)
        response_json = response.json()  # Parse the response text as JSON

        result = []

        for lang_entry in response_json:  # Iterate over each language entry in the JSON response
            lang_data = {
                "lang": lang_entry.get("lang", ""),
                "hits": []
            }

            for hit in lang_entry.get('hits', []):  # Iterate over each hit in the language entry
                hit_data = {
                    "type": hit.get("type", ""),
                    "opendict": hit.get("opendict", False),
                    "roms": []
                }

                for rom in hit.get('roms', []):  # Iterate over each rom in the hit
                    rom_data = {
                        "headword": rom.get("headword", ""),
                        "headword_full": rom.get("headword_full", ""),
                        "wordclass": rom.get("wordclass", ""),
                        "conjugation": "",
                        "verbclass": "",
                        "arabs": []
                    }

                    # Extract conjugation and verbclass from headword_full
                    headword_full = rom.get('headword_full', '')
                    patterns = {
                        'conjugation': (r'<span class=\\?"conjugation\\?"><acronym title=\\?"([^<][a-z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1)),
                        'wordclass': (r'<span class=\\?"wordclass\\?">([^<][a-zA-Z ]+)</span>', lambda match: match.group(1)),
                        'verbclass': (r'<span class=\\?"verbclass\\?"><acronym title=\\?"([^<][a-zA-Z ]+)\\?">[^<][a-z]+</acronym></span>', lambda match: match.group(1))
                    }

                    extracted_data = extract_patterns(headword_full, patterns)
                    rom_data.update(extracted_data)
                    rom_data['headword_full'] = extracted_data['text']

                    for arab in rom.get('arabs', []):  # Iterate over each arab in the rom
                        arab_data = {
                            "header": arab.get("header", ""),
                            "sense": "",
                            "entrynumber": "",
                            "reflection": "",
                            "translations": []
                        }

                        # Extract sense, entrynumber, and reflection from header
                        header = arab.get('header', '')
                        patterns = {
                            'entrynumber': (r'^\d\.', lambda match: match.group(0)),
                            'sense': (r'<span class=\\?"sense\\?">\(?(.*?)\)?</span>', lambda match: match.group(1)),
                            'reflection': (r'<span class=\\?"reflection\\?">\(?(.*?)\)?</span>', lambda match: match.group(1))
                        }

                        extracted_data = extract_patterns(header, patterns)
                        arab_data.update(extracted_data)
                        arab_data['header'] = extracted_data['text']

                        # Filter and add translations
                        for translation in arab.get('translations', []):
                            translation_data = {
                                "source": translation.get("source", ""),
                                "target": translation.get("target", "")
                            }

                            extracted_data = extract_patterns(translation_data['source'], patterns)
                            translation_data.update(extracted_data)
                            translation_data['source'] = extracted_data['text']

                            arab_data['translations'].append(translation_data)

                        rom_data["arabs"].append(arab_data)

                hit_data["roms"].append(rom_data)
            lang_data["hits"].append(hit_data)
        result.append(lang_data)

        # Print the aggregated data in JSON format
        print(json.dumps(result, ensure_ascii=False, indent=4))
        
    else:
        print(f"Error: Received status code {response.status_code}")

if __name__ == "__main__":
    run_curl_command()