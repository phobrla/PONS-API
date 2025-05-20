# PONSAPI

PONSAPI is a Python utility for automating the reconciliation of Bulgarian vocabulary flashcards with data fetched from the [PONS dictionary API](https://en.pons.com/translate). It helps language learners and lexicon curators to quickly match, validate, and annotate their flashcard collections with authoritative dictionary information. The workflow is optimized for bulk operations and integrates with both `.xlsb` Excel workbooks and JSON data.

---

## Features

- **Bulk Querying:** Fetches dictionary entries for a large set of Bulgarian terms from the PONS API.
- **Flexible Matching:** Matches flashcards against PONS data using several levels of precision (exact, partial, with/without wordclass, etc.).
- **Cutoff Logic:** Optionally trims endings (particles, clitics, etc.) and retries matches for increased robustness.
- **Binary Excel Support:** Reads `.xlsb` files with [`pyxlsb`](https://pypi.org/project/pyxlsb/); no need to convert to `.xlsx`.
- **Detailed Logging:** Outputs a timestamped log file with all operations and debug information.
- **Extensible Output:** Results can be saved in additional formats for further processing.

---

## Note on the "Anki" Table Structure

The `Flashcards.xlsb` file must contain a sheet named **"Anki"**.  
> **The "Anki" table contains 66 columns with the following headers (in order):**

1. Note ID  
2. Bulgarian 1  
3. Bulgarian 2  
4. English 1  
5. English 2  
6. English 3  
7. English 4  
8. English 5  
9. English 6  
10. PONS Status 1  
11. PONS Status 2  
12. PONS en I.1  
13. PONS en I.2  
14. PONS en I.3  
15. PONS en I.4  
16. PONS en I.5  
17. PONS en II.1  
18. PONS en II.2  
19. PONS en II.3  
20. PONS en III.1  
21. PONS en III.2  
22. PONS en III.3  
23. PONS en III.4  
24. PONS en III.5  
25. PONS en IV.1  
26. PONS en IV.2  
27. PONS en V.1  
28. PONS en>bg 1  
29. PONS en>bg 2  
30. PONS en>bg 3  
31. PONS en>bg 4  
32. PONS en>bg 5  
33. PONS en>bg 6  
34. Google Translate  
35. Wikipedia  
36. Part of Speech  
37. Type  
38. Type 2  
39. Hint  
40. Hint 2  
41. Imperfective Present  
42. Imperfective Aorist  
43. Perfective Present  
44. Perfective Aorist  
45. Adjective Masculine  
46. Adjective Feminine  
47. Adjective Neuter  
48. Adjective Plural  
49. Noun Short Definite  
50. Noun Long Definite  
51. Noun Plural  
52. Noun Numeral Plural  
53. Noun Plural Definite  
54. Noun Vocative  
55. Female Equivalent Noun Long Definite  
56. Female Equivalent Noun Plural  
57. Female Equivalent Noun Plural Definite  
58. Female Equivalent Noun Vocative  
59. Part  
60. Bulgarian Sound  
61. English Sound  
62. Bulgarian 1 Syllables  
63. Bulgarian 2 Syllables  
64. Beron Status 1  
65. Beron Status 2  
66. Tags  

> **Note:** Some versions of the table may have more or fewer columns, but this is the standard structure expected by the script.  
> Only a subset of these columns are used for PONSAPI’s processing and matching logic (e.g., "Bulgarian 1", "Part of Speech", etc.), but the file must include all columns for compatibility.

---

## Code Structure & Detailed Workflow

This section explains the inner workings of `PONSAPI.py` in detail, combining a step-by-step pseudocode walkthrough with explanations of the main components.

1. **Initialization**
    - Import standard and third-party Python libraries.
    - Define all file paths and directories (base_directory, input, output, .xlsb, etc.).
    - Configure logging (timestamped file, DEBUG level).
    - Define constants, e.g., cutoff strings for matching logic.

2. **Select Mode**
    - Set the `mode` variable at the top of the script ("fetch" or "process").

3. **Fetch Mode (`mode == "fetch"`)**
    1. Open `Inputs_for_PONS_API.txt` for reading.
    2. For each line (term) in the file:
        - Strip whitespace.
        - Skip empty terms.
        - Build the PONS API request URL with the term.
        - Set required headers (including your API key).
        - Send HTTP GET request to the PONS API.
        - If the response is HTTP 200:
            - Parse the JSON response.
            - Append a `{"query": term, "data": JSON}` object to a results list.
        - If there is an error:
            - Append `{"query": term, "data": {"error": ..., "response_text": ...}}` to the results list.
        - Log progress, especially on errors or large batches.
    3. After all terms are processed:
        - Write the results list as `concatenated.json` to the output directory.
        - Log completion of "fetch" mode.

4. **Process Mode (`mode == "process"`)**
    1. Open `concatenated.json` and parse all API results into memory.
    2. Open `Flashcards.xlsb` using `pyxlsb` (read-only).
        - Read the "Anki" worksheet row by row.
        - For each row (skip header), build a dictionary with fields like "Bulgarian 1", "Bulgarian 2", "Part of Speech", and "Note ID".
        - Store all flashcards in a list.
        - Log the number of flashcards loaded.
    3. For each flashcard in the list:
        - Extract the values for "Bulgarian 1" and "Part of Speech" (and others as needed).
        - Initialize variables for match status, hints, etc.
        - For each entry in `concatenated.json`:
            - Extract the query term and PONS data.
            - **Matching Logic:** Try each level in order (stop after the first match):
                1. **Level 1:** Check if flashcard term equals query term **and** part of speech matches.
                    - If so, record as Level 1 match, extract possible hints, break loop.
                2. **Level 2:** If not matched, check if flashcard term equals query term (ignore part of speech).
                    - If so, record as Level 2 match, extract hints, break loop.
                3. **Level 3:** If not matched, try partial matching (look for collocations, indirect references, reflections, etc. in the PONS JSON).
                    - If found, record as Level 3 match, extract hints, break loop.
                4. **Level 4:** If not matched, apply cutoff logic:
                    - For each cutoff string (e.g., " се", " си", etc.):
                        - If the flashcard term ends with a cutoff, remove it and retry Levels 1–3 with the revised term.
                        - If matched, record as Level 4 match, extract hints, break loop.
                5. If still no match, record as unmatched.
            - Log which level was matched, what hints were found, and any notes (e.g., cutoff applied).
        - Repeat for the next flashcard.
    4. After all flashcards are processed:
        - Log summary statistics (number of matches at each level, unmatched cards, etc.).
        - Optionally, write results to a file (logs by default; can be extended to CSV/XLSX).

5. **Unknown Mode**
    - If the mode is not recognized, log an error.

6. **End Script**

**Key Functions:**
- `fetch_and_concatenate()`: Handles all API fetching and concatenation into a single JSON file.
- `process_and_reconcile()`: Handles all logic for matching flashcards with API data.
- `extract_roms()`, `extract_wordclass()`, `match_partial()`, `apply_cutoff_logic()`: Helpers for parsing and matching.

**Notes on Extending:**
- To write results back to Excel, export to `.xlsx` and use `openpyxl`.
- To support more advanced Unicode or error handling, extend the relevant I/O sections.
- To speed up API calls, consider batching or async requests.

*For details on things that do not work or should be avoided, see the “Things That Don’t Work” section below.*

---

## Requirements

- Python 3.7+
- [requests](https://pypi.org/project/requests/)
- [pyxlsb](https://pypi.org/project/pyxlsb/)
- (Optional, for `.xlsx` support) [openpyxl](https://pypi.org/project/openpyxl/)

Install dependencies (preferably in a virtual environment):

```sh
pip install requests pyxlsb openpyxl
```

---

## File Structure

- **PONSAPI.py** – Main Python script.
- **Inputs_for_PONS_API.txt** – List of Bulgarian terms (one per line) to query.
- **PONS json Files/** – Directory where fetched PONS API results are stored as JSON.
- **Flashcards.xlsb** – Your flashcard database (must have a sheet named "Anki").
- **Query Parts of Speech.json** – (Optional) Stores mappings for parts of speech.
- **debug_YYYYMMDDTHHMMSS.log** – Log file for each run.

---

## Usage

### 1. Prepare your files

- Place all files in the directories specified in the script, or modify the paths at the top of `PONSAPI.py`.
- `Flashcards.xlsb` must have a sheet named `Anki` with at least these columns:  
  **"Bulgarian 1"**, **"Bulgarian 2"**, **"Part of Speech"**, **"Note ID"**  
  (See the full 66-column list in the section above.)

### 2. Fetch PONS data

Set the mode at the top of `PONSAPI.py`:

```python
mode = "fetch"
```

Run the script:

```sh
python PONSAPI.py
```

This will:
- Read terms from `Inputs_for_PONS_API.txt`
- Fetch their dictionary entries from the PONS API
- Save all results in `PONS json Files/concatenated.json`

### 3. Reconcile flashcards with dictionary data

Set the mode to `process`:

```python
mode = "process"
```

Run again:

```sh
python PONSAPI.py
```

This will:
- Load your flashcards from `Flashcards.xlsb`
- Compare each entry with the fetched PONS API data
- Attempt several match strategies (exact, partial, cutoff)
- Log detailed results and progress

### 4. Review Results

- The script logs all actions to a new `debug_YYYYMMDDTHHMMSS.log` file in your base directory.
- (Optional) The results can be extended to write to a new worksheet or file for further analysis.

---

## Matching Logic (Summary)

1. **Level 1:** Exact match on term and part of speech.
2. **Level 2:** Exact match on term, different part of speech.
3. **Level 3:** Partial matches via indirect references, collocations, etc.
4. **Level 4:** Applies cutoff logic (removes certain endings) and retries matching.

All matching steps are logged for transparency.

---

## Configuration

- All file paths are set at the top of `PONSAPI.py`. Adjust as needed for your environment.
- Logging is set to `DEBUG` and creates a new log file for every run.
- The PONS API secret key must be set in the script (replace `"XXX"` with your actual key).

---

## Limitations

- Writes results to logs only by default. Modify or extend the script to write results to an output sheet or another file type if needed.
- Large `.xlsb` files may take significant time to process (progress is logged).
- Only supports `.xlsb` for reading. If you want to write back to Excel, use `.xlsx` and [`openpyxl`](https://pypi.org/project/openpyxl/).

---

## Things That Don’t Work

This section documents approaches and coding attempts that were tried in this project but **did not work**. These notes are here to remind me never to return to these methods or patterns.

- **Using openpyxl with `.xlsb` files:**  
  *openpyxl* does **not** support reading or writing Excel binary workbook files (`.xlsb`). Attempts to use openpyxl led to errors like  
  `openpyxl does not support binary format .xlsb, please convert this file to .xlsx format if you want to open it with openpyxl`.  
  **Never use openpyxl with .xlsb. Use pyxlsb for reading .xlsb files.**

- **Writing back to `.xlsb` files**:  
  There is **no reliable library** in Python for writing data back to `.xlsb` files. pyxlsb can only read. Attempts to write results to `.xlsb` failed or resulted in corrupted files.  
  **Do not attempt to write to .xlsb. If output to Excel is required, convert to `.xlsx` and use openpyxl or another suitable library.**

- **Mixing openpyxl and pyxlsb in the same workflow:**  
  Trying to use both libraries for the same file or in the same read/write loop leads to confusion and errors, especially regarding file handles and memory.  
  **Stick to one library per file and workflow.**

- **Expecting pyxlsb to handle formulas, formatting, or anything but basic values:**  
  pyxlsb is limited to extracting cell values only. It does **not** support writing, nor does it preserve formatting or formulas.  
  **Do not rely on pyxlsb for anything except simple cell value reads.**

- **Naive Unicode/encoding handling for large `.xlsb` or text files:**  
  Not explicitly specifying encoding or not handling Unicode issues caused failures on non-ASCII flashcards or API results.  
  **Always use UTF-8 and handle decoding errors as needed.**

- **Sequential API fetching for very large input lists:**  
  Fetching thousands of terms from the PONS API sequentially without batching or rate-limiting can be extremely slow and/or lead to throttling.  
  **Don’t fetch large lists in one go without considering batching or respecting API limits.**

- **Assuming API or Excel column order is fixed:**  
  Hard-coding column indices led to mismatches when the underlying Excel schema changed.  
  **Always verify header rows and use header names, not indices.**

- **Saving results only to logs:**  
  Relying solely on logs for output made it hard to analyze or use results programmatically.  
  **Always build an explicit export step (CSV, XLSX, or JSON) for results.**

---

*This section is a living document. If you try something and it fails, document it here so you won’t repeat past mistakes!*

---

## Troubleshooting

- **No output or only a few log lines?**
  - Check that your input files exist at the specified paths.
  - Inspect the log file for any errors.
- **openpyxl error about .xlsb?**
  - This script uses `pyxlsb` and does not require `.xlsx` conversion for reading.
- **API errors?**
  - Make sure your PONS API key is valid and not rate-limited.
- **Performance issues?**
  - For very large flashcard sets, run the process overnight or in batches.

---

## Regex to Extract "title" from `<acronym>` Tags

This project provides a regular expression for extracting the content of the `title` attribute from HTML `<acronym>` tags, discarding the tags themselves and their inner content.

### Purpose

When processing HTML, you may want to remove `<acronym>` tags but retain only the value from their `title` attribute. This is useful for text extraction, simplifying markup, or transforming HTML for text-only outputs.

### Regular Expression

```regex
<acronym[^>]*title=["']([^"']+)["'][^>]*>.*?<\/acronym>
```

#### How It Works

- `<acronym`: Matches the start of an `<acronym>` tag.
- `[^>]*`: Matches any tag attributes.
- `title=["']([^"']+)["']`: Captures the value of the `title` attribute in group 1.
- `[^>]*`: Consumes any additional attributes or spaces.
- `>.*?<\/acronym>`: Matches the tag content and the closing `</acronym>`.

### Usage Example

#### Python

```python
import re

html = '<acronym title="Example Title">Some content</acronym>'
result = re.sub(r'<acronym[^>]*title=["\']([^"\']+)["\'][^>]*>.*?<\/acronym>', r'\1', html)
print(result)  # Output: Example Title
```

### Limitations

- Assumes the `title` attribute is always present.
- Does not handle nested `<acronym>` tags.
- Not suitable for parsing ambiguous or malformed HTML. For full HTML parsing, use a dedicated HTML parser like BeautifulSoup.

### License

This project is provided under the MIT License.

---

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

## Author

Created by [phobrla](https://github.com/phobrla).

---

## Contributing

Pull requests, bug reports, and suggestions are welcome!
