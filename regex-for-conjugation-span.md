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

**Filename to use:**  
`regex-for-conjugation-span.md`
