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

## Troubleshooting

- **No output or only a few log lines?**
  - Check that your input files exist at the specified paths.
  - Inspect the log file for any errors.
- **openpyxl error about .xlsb?**
  - This script uses `pyxlsb` and does not require `.xlsx` conversion.
- **API errors?**
  - Make sure your PONS API key is valid and not rate-limited.
- **Performance issues?**
  - For very large flashcard sets, run the process overnight or in batches.

---

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

## Author

Created by [phobrla](https://github.com/phobrla).

---

## Contributing

Pull requests, bug reports, and suggestions are welcome!
