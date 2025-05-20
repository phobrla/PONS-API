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
<details>
<summary>Show/Hide Columns</summary>

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
</details>

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

---

## Regex and HTML Extraction Reference

This section contains reference material and examples for regexes, HTML parsing/extraction, and data mapping relevant to the PONSAPI workflow and acronym-expansion logic.

### Extant

These regexes and guides are relevant for the current approach, where all acronyms are expanded and normalized in the data.

#### Regex to Extract "title" from `<acronym>` Tags

Extract the content of the `title` attribute from HTML `<acronym>` tags, discarding the tags themselves and their inner content.

```regex
<acronym[^>]*title=["']([^"']+)["'][^>]*>.*?<\/acronym>
```

**Python Example:**
```python
import re

html = '<acronym title="Example Title">Some content</acronym>'
result = re.sub(r'<acronym[^>]*title=["\']([^"\']+)["\'][^>]*>.*?<\/acronym>', r'\1', html)
print(result)  # Output: Example Title
```

#### Superscript Representation Guide

This document describes how to represent superscripts such as `<sup>1</sup>`, `<sup>2</sup>`, and `<sup>3</sup>` in JSON.

**Superscript HTML Example:**
```html
<sup>1</sup>
<sup>2</sup>
<sup>3</sup>
```
**Superscript in JSON:**
```json
{
  "sup": ["1", "2", "3"]
}
```

---

### Legacy

<details>
<summary>Show legacy regex and extraction patterns (click to expand)</summary>

The following regexes and patterns relate to legacy approaches, including partial or ambiguous acronym expansion and mixed-content `<span>` extraction. These are kept for reference or for use if you need to match or parse pre-expansion data.

#### Regex for Matching Conjugation `<span>` Patterns

This regex matches either of these two HTML patterns and captures the aspect as a group:

- `<span class="conjugation"><acronym title="imperfective form">imperf</acronym></span>`
- `<span class="conjugation"><acronym title="perfective form">perf</acronym></span>`

**Regex:**
```regex
<span class="conjugation"><acronym title="(imperfective form|perfective form)">(imperf|perf)</acronym></span>
```

**Capturing Groups:**
1. Aspect string – `imperfective form` or `perfective form`
2. Abbreviation – `imperf` or `perf`

---

#### Regex to Find `<span>` Elements with Multiple `<acronym>` Tags

```regex
<span\b[^>]*>(?:[^<]*<acronym\b[^>]*>.*?<\/acronym>[^<]*){2,}<\/span>
```
- Matches `<span>` elements containing two or more `<acronym>` tags (and their contents).
- Does **not** match `<span>` elements with only one or zero `<acronym>` tags.

---

#### Regex for Matching Span and Acronym Patterns

This regex matches both plain text and acronym-containing spans, especially in pairs divided by `/`.

```regex
<span class=\\\"info\\\">(?:[^<]+|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)</span> ?/ ?<span class=\\\"[^<]*\\\">(?:[^<]*|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)</span>
```

---

#### Combined Regex Pattern

```regex
<span class=\\"info\\">([^<]*|<acronym title=\\"([A-Za-zА-Яа-я :,\\\\.]*)\\">[A-Za-zА-Яа-я]+</acronym>)</span>
```
- Matches either plain text or an acronym-containing span for class "info".

---

#### HTML Acronym Regex Reference

This document lists how to match specific HTML-acronym patterns in (JSON-escaped) HTML using regex.  
For the full table of patterns and their corresponding regex, see [html-acronym-regex-reference.csv](html-acronym-regex-reference.csv).

---

#### Special/Combined Regex for `<span class="info">`

To match cases where the `title` attribute is empty or filled:

```regex
<span class=\"info\"><acronym title=\"([A-Za-zА-Яа-я :,\\.]*)\">[A-Za-zА-Яа-я]+</acronym>
```

---

#### Optional & Generalized Acronym Regex Patterns

These regex patterns match `<span>` elements with optional `<acronym>` tags inside, and can be used as generalized replacements for extracting content from various `<span>` elements with specific classes.

```regex
<span class=\\"conjugation\\">(?:([^<]*)|<acronym title=\\"((?:imperfective form|perfective form))\\">((?:imperf|perf))</acronym>)</span>
<span class=\\"example\\">(?:([^<]*)|<acronym title=\\"([А-Яа-я ]+)\\">([А-Яа-я]+)</acronym>)</span>
<span class=\\"genus\\">(?:([^<]*)|<acronym title=\\"([A-Za-z ]+)\\">([A-Za-z]+)</acronym>)</span>
<span class=\\"idiom_proverb\\">(?:([^<]*)|<acronym title=\\"([А-Яа-я ]+)\\">([А-Яа-я]+)</acronym>)</span>
<span class=\\"number\\">(?:([^<]*)|<acronym title=\\"([A-Za-z]+)\\">([A-Za-z]+)</acronym>)</span>
<span class=\\"or\\">(?:([^<]*)|<acronym title=\\"([A-Za-zА-Яа-я]+)\\">([A-Za-zА-Яа-я\\.]+)</acronym>)</span>
<span class=\\"reference_qualification\\">(?:([^<]*)|<acronym title=\\"([А-Яа-я ]+)\\">([А-Яа-я]+)</acronym>)</span>
<span class=\\"region\\">(?:([^<]*)|<acronym title=\\"([A-Za-z]+)\\" class=\\"[A-Za-z]+\\">([A-Za-z]+)</acronym>)</span>
<span class=\\"rhetoric\\">(?:([^<]*)|<acronym title=\\"([A-Za-zА-Яа-я]+)\\">([A-Za-zА-Яа-я]+)</acronym>)</span>
<span class=\\"style\\">(?:([^<]*)|<acronym title=\\"([A-Za-zА-Яа-я ]+)\\">([A-Za-zА-Яа-я]+)</acronym>)</span>
<span class=\\"topic\\">(?:([^<]*)|<acronym title=\\"([A-Za-z ,]+)\\">([A-Za-z]+)</acronym>)</span>
<span class=\\"verbclass\\">(?:([^<]*)|<acronym title=\\"([A-Za-z ]+ verb)\\">([A-Za-z]+)</acronym>)</span>
<span class=\\"wordclass\\">(?:([^<]*)|<acronym title=\\"([A-Za-z ]+)\\">([A-Za-z]+)</acronym>)</span>
```

And, in a more general form:

```regex
<span class=\"conjugation\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"example\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"genus\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"genus\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"idiom_proverb\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"info\">([^<]*|<acronym title=\"([^< :,\\.\\\\]*)\">([^<]+)</acronym>)</span>
<span class=\"number\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"or\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<\\.]+)</acronym>)</span>
<span class=\"reference_qualification\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"region\">(?:([^<]*)|<acronym title=\"([^<]+)\" class=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"rhetoric\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"style\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"topic\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"topic\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"verbclass\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
<span class=\"wordclass\">(?:([^<]*)|<acronym title=\"([^<]+)\">([^<]+)</acronym>)</span>
```

**Notes:**
- For each regex:
  - The first capturing group is the plain text (when no acronym is present).
  - The second capturing group is the acronym's `title` attribute (if present).
  - The third capturing group is the acronym's display text (if present).
- All character class ranges like `[А-Яа-я]+`, `[A-Za-z]+`, or `[A-Za-zА-Яа-я]+` have been replaced with `[^<]+` in the generalized form for flexibility.

#### Acronym Conversion Reference Table

See [Acronyms.json](Acronyms.json) for the complete set of conversion mappings and example JSON structures showing how `<span>` and nested `<acronym>` tags with titles and contents can be represented as JSON objects, grouped by their parent span class.

</details>

---

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

## Author

Created by [phobrla](https://github.com/phobrla).

---

## Contributing

Pull requests, bug reports, and suggestions are welcome!
