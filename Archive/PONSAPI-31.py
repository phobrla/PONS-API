# CSV Loading in reconcile_entries()
try:
    with open(query_parts_of_speech_csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            bulgarian_word = row.get("Bulgarian", "").strip()
            part_of_speech = row.get("Part of Speech", "").strip()
            if bulgarian_word and part_of_speech:
                bulgarian_to_pos[bulgarian_word] = part_of_speech
    logging.debug(f"Total mappings in Query Parts of Speech.csv: {len(bulgarian_to_pos)}")
    logging.debug(f"Sample mappings from Query Parts of Speech.csv: {list(bulgarian_to_pos.items())[:5]}")
except (IOError, UnicodeDecodeError) as e:
    logging.error(f"Error reading CSV file '{query_parts_of_speech_csv_path}': {e}")
    return