def process_bulgarian_field(bulgarian_field, concatenated_data):
    """
    Processes a single Bulgarian field (Bulgarian 1 or Bulgarian 2).
    Checks its presence and status in concatenated.json.

    """
    if not bulgarian_field:
        return "Missing"

    # Search for the query in concatenated.json
    concatenated_entry = next((item for item in concatenated_data if item.get("query") == bulgarian_field), None)

    if not concatenated_entry:
        return "Missing"

    # Check the contents of the data field
    data = concatenated_entry.get("data", {})
    if isinstance(data, dict):
        # Explicitly check for the "Received status code 204" error
        if data.get("error") == "Received status code 204":
            return "Not Found"
    elif isinstance(data, list):
        # Check if there are no hits
        hits = [item.get("hits", []) for item in data]
        if not any(hits):  # No hits at all
            return "No Headword"
        # Check for roms in hits
        if any("roms" in hit for sublist in hits for hit in sublist):
            return "Found"

    # If none of the above conditions match, assume "No Headword"
    return "No Headword"