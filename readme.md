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
<!-- [columns omitted for brevity, unchanged from previous versions] -->

---

## Code Structure & Detailed Workflow

<!-- [unchanged, omitted for brevity] -->

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

<!-- [unchanged, omitted for brevity] -->

---

## Regex to Extract "title" from `<acronym>` Tags

<!-- [unchanged, omitted for brevity] -->

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

<!-- [unchanged, omitted for brevity] -->

---

## Acronym Conversion Reference Table

<!-- [unchanged, omitted for brevity] -->

---

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

## Author

Created by [phobrla](https://github.com/phobrla).

---

## Contributing

Pull requests, bug reports, and suggestions are welcome!
