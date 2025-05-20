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

# Regex for Matching Conjugation `<span>` Patterns

This regex matches either of these two HTML patterns and captures the aspect as a group:

- `<span class="conjugation"><acronym title="imperfective form">imperf</acronym></span>`
- `<span class="conjugation"><acronym title="perfective form">perf</acronym></span>`

## Regex

```regex
<span class="conjugation"><acronym title="(imperfective form|perfective form)">(imperf|perf)</acronym></span>
```

### Capturing Groups

1. **First group**: Captures the aspect string – either `imperfective form` or `perfective form`.
2. **Second group**: Captures the abbreviation – either `imperf` or `perf`.

## Usage Example

You can use this regex in most languages with minor adjustments for escaping if needed. For example, in Python:

```python
import re

pattern = r'<span class="conjugation"><acronym title="(imperfective form|perfective form)">(imperf|perf)</acronym></span>'
text = '<span class="conjugation"><acronym title="imperfective form">imperf</acronym></span>'

match = re.search(pattern, text)
if match:
    print("Aspect:", match.group(1))
    print("Abbreviation:", match.group(2))
```

---

## Regex to Find `<span>` Elements with Multiple `<acronym>` Tags

This document explains how to use a regex to find HTML `<span>` elements that contain more than one `<acronym>` tag, and demonstrates correct and incorrect matches.

---

### Regex Pattern

```regex
<span\b[^>]*>(?:[^<]*<acronym\b[^>]*>.*?<\/acronym>[^<]*){2,}<\/span>
```

#### Explanation

- `<span\b[^>]*>`  
  Matches the opening `<span>` tag with optional attributes.

- `(?:[^<]*<acronym\b[^>]*>.*?<\/acronym>[^<]*){2,}`  
  Non-capturing group to match at least two `<acronym>` tags (and their content) within the same `<span>`.  
  - `[^<]*` matches any non-tag text between tags.
  - `<acronym\b[^>]*>` matches the opening `<acronym>` tag with optional attributes.
  - `.*?<\/acronym>` matches the content and the closing `</acronym>` tag.

- `<\/span>`  
  Matches the closing `</span>` tag.

---

### Example Usage in Python

```python
import re

html = '''
<span class="rhetoric"><acronym title="също">и</acronym> <acronym title="figurative">fig</acronym></span>
<span class="wordclass"><acronym title="adjective">ADJ</acronym></span>
<span class="topic"><acronym title="technology">TECH</acronym>, <acronym title="computing">COMPUT</acronym></span>
<span class="flexion">&lt;-ът&gt;</span>
'''

pattern = r'<span\b[^>]*>(?:[^<]*<acronym\b[^>]*>.*?<\/acronym>[^<]*){2,}<\/span>'

matches = re.findall(pattern, html, re.DOTALL)
for match in matches:
    print(match)
```

---

### Correct Match Example

```html
<span class="rhetoric"><acronym title="също">и</acronym> <acronym title="figurative">fig</acronym></span>
```

---

### Incorrect Match Examples (these will **not** match)

```html
<span class="wordclass"><acronym title="adjective">ADJ</acronym></span>
<span class="genus"><acronym title="masculine">m</acronym></span>
<span class="flexion">&lt;-ът&gt;</span>
```

---

### Additional Notes

- The regex will **not match** `<span>` elements that contain only one or zero `<acronym>` tags.
- It is robust against unrelated `<span>` tags in the same HTML block.
- For complex or malformed HTML, consider using an HTML parser (like BeautifulSoup in Python) for greater accuracy.

---

## Regex for Matching Span and Acronym Patterns

This regex is designed to match the following HTML patterns (with double backslashes for escaping):

- `<span class=\"info\">SomeText</span> / <span class=\"other\">OtherText</span>`
- `<span class=\"info\"><acronym title=\"също\">и</acronym></span> / <span class=\"info\"><acronym title=\"...\">...</acronym></span>`

### Pattern

```regex
<span class=\\\"info\\\">(?:[^<]+|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)</span> ?/ ?<span class=\\\"[^<]*\\\">(?:[^<]*|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)</span>
```

### Explanation

- `<span class=\\\"info\\\">`: Matches a `<span>` tag with the class `info` (escaped).
- `(?:[^<]+|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)`:
  - `[^<]+`: Matches any text content that does not include a `<` character.
  - `<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>`: Matches an `<acronym>` tag with a `title` attribute containing Cyrillic or Latin characters, spaces, commas, colons, backslashes, or periods, and containing Cyrillic or Latin text content.
- `</span> ?/ ?`: Matches the closing `</span>` tag, a slash (`/`), and optional spaces.
- `<span class=\\\"[^<]*\\\">`: Matches another `<span>` tag with any class name.
- `(?:[^<]*|<acronym title=\\\"([A-Za-zА-Яа-я :,\\\\.]*)\\\">[A-Za-zА-Яа-я]+</acronym>)`: Matches either plain text or another `<acronym>` tag as described above.
- `</span>`: Matches the closing `</span>` tag.

### Usage

- This pattern can be used to match both simple text and acronym-containing spans on either side of a `/`.
- The double backslashes ensure compatibility with environments that require double-escaping (e.g., in a string literal in some languages or regex engines).

### Example Matches

- `<span class=\"info\">отр</span> / <span class=\"other\">some text</span>`
- `<span class=\"info\"><acronym title=\"също\">и</acronym></span> / <span class=\"info\"><acronym title=\"също\">и</acronym></span>`

### Notes

- Adjust `[A-Za-zА-Яа-я :,\\\\.]*` for stricter or broader title attribute matching if needed.
- This pattern is flexible for a wide range of similar HTML constructs.

---

## Combined Regex Pattern

You can combine the two regex patterns into one using an alternation (`|`) to account for both patterns. Here is the combined regex:

```regex
<span class=\\"info\\">([^<]*|<acronym title=\\"([A-Za-zА-Яа-я :,\\\\.]*)\\">[A-Za-zА-Яа-я]+</acronym>)</span>
```

### Explanation

1. **Outer `<span>` tag**: `<span class=\\"info\\">` and `</span>` are the same for both patterns.
2. **Alternation (`|`)**:
    - The first part matches: `[^<]*` (no `<` characters inside the span).
    - The second part matches: `<acronym title=\\"([A-Za-zА-Яа-я :,\\\\.]*)\\">[A-Za-zА-Яа-я]+</acronym>`.

This combined regex will match either of the two patterns inside the `<span>` tag.

---

## HTML Acronym Regex Reference

This document lists how to match specific HTML-acronym patterns in (JSON-escaped) HTML using regex.  
For the full table of patterns and their corresponding regex, see [html-acronym-regex-reference.csv](html-acronym-regex-reference.csv).

---

## Special/Combined Regex for `<span class="info">`

To match both cases where the `title` attribute is empty or filled (e.g. `или`):

```regex
<span class=\"info\"><acronym title=\"([A-Za-zА-Яа-я :,\\.]*)\">[A-Za-zА-Яа-я]+</acronym>
```

- The `*` after the character class means it matches both empty and non-empty titles.

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

## Optional Acronym Regex Patterns

The following regex patterns match `<span>` elements with optional `<acronym>` tags inside.  
For each, the acronym is optional. The regex captures the acronym's `title` attribute and the main content within the `<span>`.  
All other groups are non-capturing.  
The escaped `\\"` format is retained for compatibility.

---

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

---

## Notes

- For each regex:
  - The first capturing group is the plain text (when no acronym is present).
  - The second capturing group is the acronym's `title` attribute (if present).
  - The third capturing group is the acronym's display text (if present).
  - Everything else is in a non-capturing group.

- These patterns allow you to reliably extract either the plain text or the acronym details from the HTML.

---

## Generalized Regex Replacements for `<span>` Patterns

This document provides generalized regex patterns for extracting content from various `<span>` elements with specific classes. The patterns are updated to use `[^<]+` instead of any language-specific character classes (such as `[А-Яа-я]+`, `[A-Za-z]+`, or `[A-Za-zА-Яа-я]+`) for greater flexibility and coverage.

---

## Regex Patterns

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

---

## Notes

- All character class ranges like `[А-Яа-я]+`, `[A-Za-z]+`, or `[A-Za-zА-Яа-я]+` have been replaced with `[^<]+` to match any sequence of characters that does not include the `<` character.
- This generalization increases the robustness and flexibility of the patterns, allowing them to match a wider range of content regardless of language or alphabet.
- The structure of the regex for each `<span>` type remains the same; only the inner matching logic has been generalized.

---

## Superscript Representation Guide

This document describes how to represent superscripts such as `<sup>1</sup>`, `<sup>2</sup>`, and `<sup>3</sup>` in JSON.

### Superscript HTML

```html
<sup>1</sup>
<sup>2</sup>
<sup>3</sup>
```

### Superscript in JSON

The superscript values can be represented in JSON as follows:

```json
{
  "sup": ["1", "2", "3"]
}
```

Each value in the `"sup"` array corresponds to the content inside a `<sup>` HTML tag.

### Example Usage

If you need to represent a series of superscript references, include them as shown above.

For example, if you want to indicate that a word or phrase has three superscript references, you might include:

```json
{
  "word": "example",
  "sup": ["1", "2", "3"]
}
```

### Notes

- This approach is simple and extensible for any number of superscripts.
- If you need to associate the superscript with additional information (such as footnote content), consider using an array of objects, e.g.:

```json
{
  "superscripts": [
    {"value": "1", "note": "First footnote"},
    {"value": "2", "note": "Second footnote"},
    {"value": "3", "note": "Third footnote"}
  ]
}
```

---

## Acronym Conversion Reference Table

Below are example JSON structures showing how `<span>` and nested `<acronym>` tags with titles and contents can be represented as JSON objects, grouped by their parent span class.

```json
{"span class":"conjugation","children":[{"Acronym Title":"imperfective form","Acronym Content":"imperf"},{"Acronym Title":"perfective form","Acronym Content":"perf"}]}
{"span class":"example","children":[{"Acronym Title":"нещо","Acronym Content":"нщ"},{"Acronym Title":"някого","Acronym Content":"нкг"},{"Acronym Title":"някому","Acronym Content":"нкм"},{"Acronym Title":"също","Acronym Content":"и"}]}
{"span class":"genus","children":[{"Acronym Title":"feminine","Acronym Content":"f"},{"Acronym Title":"masculine and feminine","Acronym Content":"mf"},{"Acronym Title":"masculine","Acronym Content":"m"},{"Acronym Title":"neuter","Acronym Content":"nt"}]}
{"span class":"idiom_proverb","children":[{"Acronym Title":"нещо","Acronym Content":"нщ"},{"Acronym Title":"някого","Acronym Content":"нкг"},{"Acronym Title":"също","Acronym Content":"и"}]}
{"span class":"info","children":[{"Acronym Title":"[blank]","Acronym Content":"или"},{"Acronym Title":"abbreviation of","Acronym Content":"abbrev of"},{"Acronym Title":"accusative","Acronym Content":"acc"},{"Acronym Title":"countable","Acronym Content":"count:"},{"Acronym Title":"dative","Acronym Content":"dat"},{"Acronym Title":"no plural","Acronym Content":"no pl"},{"Acronym Title":"usually","Acronym Content":"usu"},{"Acronym Title":"виж","Acronym Content":"вж."},{"Acronym Title":"множествено число","Acronym Content":"pl"},{"Acronym Title":"множествено число","Acronym Content":"мн"},{"Acronym Title":"също","Acronym Content":"и"}]}
{"span class":"number","children":[{"Acronym Title":"plural","Acronym Content":"pl"}]}
{"span class":"or","children":[{"Acronym Title":"or","Acronym Content":"or"},{"Acronym Title":"или","Acronym Content":"o."}]}
{"span class":"reference_qualification","children":[{"Acronym Title":"множествено число","Acronym Content":"мн"}]}
{"span class":"region","children":[{"Acronym Title":"Irish\" class=\"Irish","Acronym Content":"Irish"}]}
{"span class":"rhetoric","children":[{"Acronym Title":"figurative","Acronym Content":"fig"},{"Acronym Title":"ironic","Acronym Content":"iron"},{"Acronym Title":"pejorative","Acronym Content":"pej"},{"Acronym Title":"proverb","Acronym Content":"prov"},{"Acronym Title":"също","Acronym Content":"и"}]}
{"span class":"style","children":[{"Acronym Title":"formal language","Acronym Content":"form"},{"Acronym Title":"informal","Acronym Content":"inf"},{"Acronym Title":"literary","Acronym Content":"liter"},{"Acronym Title":"slang","Acronym Content":"sl"},{"Acronym Title":"vulgar","Acronym Content":"vulg"},{"Acronym Title":"също","Acronym Content":"и"}]}
{"span class":"topic","children":[{"Acronym Title":"administration","Acronym Content":"ADMIN"},{"Acronym Title":"anatomy","Acronym Content":"ANAT"},{"Acronym Title":"architecture","Acronym Content":"ARCHIT"},{"Acronym Title":"art","Acronym Content":"ART"},{"Acronym Title":"astrology, astronomy","Acronym Content":"ASTRO"},{"Acronym Title":"automobile, transport","Acronym Content":"AUTO"},{"Acronym Title":"aviation","Acronym Content":"AVIAT"},{"Acronym Title":"biology","Acronym Content":"BIOL"},{"Acronym Title":"botany","Acronym Content":"BOT"},{"Acronym Title":"chemistry","Acronym Content":"CHEM"},{"Acronym Title":"commerce","Acronym Content":"COMM"},{"Acronym Title":"computing","Acronym Content":"COMPUT"},{"Acronym Title":"construction","Acronym Content":"CONSTR"},{"Acronym Title":"ecology","Acronym Content":"ECOL"},{"Acronym Title":"economy","Acronym Content":"ECON"},{"Acronym Title":"electricity, electrical engineering","Acronym Content":"ELEC"},{"Acronym Title":"film, cinema","Acronym Content":"CINE"},{"Acronym Title":"finance","Acronym Content":"FIN"},{"Acronym Title":"food and cooking","Acronym Content":"FOOD"},{"Acronym Title":"geography","Acronym Content":"GEOG"},{"Acronym Title":"geology","Acronym Content":"GEOL"},{"Acronym Title":"history","Acronym Content":"HISTORY"},{"Acronym Title":"industry","Acronym Content":"INDUST"},{"Acronym Title":"law","Acronym Content":"LAW"},{"Acronym Title":"linguistics, grammar","Acronym Content":"LING"},{"Acronym Title":"literature","Acronym Content":"LIT"},{"Acronym Title":"mathematics","Acronym Content":"MATH"},{"Acronym Title":"medicine","Acronym Content":"MED"},{"Acronym Title":"meteorology","Acronym Content":"METEO"},{"Acronym Title":"military","Acronym Content":"MIL"},{"Acronym Title":"mining, mineralogy","Acronym Content":"MIN"},{"Acronym Title":"music","Acronym Content":"MUS"},{"Acronym Title":"mythology","Acronym Content":"MYTH"},{"Acronym Title":"nautical, naval","Acronym Content":"NAUT"},{"Acronym Title":"philosophy","Acronym Content":"PHILOS"},{"Acronym Title":"photography","Acronym Content":"PHOTO"},{"Acronym Title":"physics","Acronym Content":"PHYS"},{"Acronym Title":"politics","Acronym Content":"POL"},{"Acronym Title":"psychology","Acronym Content":"PSYCH"},{"Acronym Title":"radio broadcasting","Acronym Content":"RADIO"},{"Acronym Title":"railway","Acronym Content":"RAIL"},{"Acronym Title":"religion","Acronym Content":"REL"},{"Acronym Title":"school, education","Acronym Content":"SCHOOL"},{"Acronym Title":"sociology","Acronym Content":"SOCIOL"},{"Acronym Title":"sports","Acronym Content":"SPORTS"},{"Acronym Title":"technology","Acronym Content":"TECH"},{"Acronym Title":"telecommunications","Acronym Content":"TELEC"},{"Acronym Title":"television","Acronym Content":"TV"},{"Acronym Title":"theatre","Acronym Content":"THEAT"},{"Acronym Title":"typography, printing","Acronym Content":"TYPO"},{"Acronym Title":"university","Acronym Content":"UNIV"},{"Acronym Title":"zoology","Acronym Content":"ZOOL"}]}
{"span class":"verbclass","children":[{"Acronym Title":"impersonal verb","Acronym Content":"impers"},{"Acronym Title":"intransitive verb","Acronym Content":"intr"},{"Acronym Title":"reflexive verb","Acronym Content":"refl"},{"Acronym Title":"transitive verb","Acronym Content":"trans"}]}
{"span class":"wordclass","children":[{"Acronym Title":"adjective","Acronym Content":"ADJ"},{"Acronym Title":"adverb","Acronym Content":"ADV"},{"Acronym Title":"conjunction","Acronym Content":"CONJ"},{"Acronym Title":"noun","Acronym Content":"N"},{"Acronym Title":"numeral","Acronym Content":"NUM"},{"Acronym Title":"particle","Acronym Content":"PARTICLE"},{"Acronym Title":"pronoun","Acronym Content":"PRON"}]}
```

---

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

## Author

Created by [phobrla](https://github.com/phobrla).

---

## Contributing

Pull requests, bug reports, and suggestions are welcome!
