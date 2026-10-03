# Structured Output Extraction Pipeline

Turn messy, unstructured text into **validated, structured data** using an LLM (Google Gemini) and Pydantic.

Real-world text such as emails, invoices and chat messages is inconsistent. LLMs understand it well but can return wrong formats or invent values. This pipeline adds a schema, validation and a repair loop so the output is reliable enough to feed into databases and analytics.

## Example

**Input (messy email):**

```
hey, pls find attached inv #INV-2041 from Acme Supplies dated 3rd Sept 2026.
total comes to Rs 12,450 incl. GST, payment due in 15 days. thanks, Ravi
```

**Output (validated JSON):**

```json
{
  "source": "email1.txt",
  "invoice_number": "INV-2041",
  "vendor": "Acme Supplies",
  "invoice_date": "2026-09-03",
  "total_amount": 12450.0,
  "currency": "INR",
  "due_days": 15
}
```

## How it works

1. **Schema:** `schemas.py` defines the exact fields and rules with Pydantic (for example `total_amount > 0`, a 3-letter currency code, a valid date).
2. **Extraction:** `extractor.py` sends the raw text to Gemini in JSON mode with the schema in the system prompt.
3. **Validation:** the response is validated against the schema.
4. **Repair loop:** if validation fails, the error message is sent back to the model so it can correct its answer (up to 3 attempts).
5. **API resilience:** temporary API errors (429, 500, 503) are retried with exponential backoff.
6. **Output:** valid records are written to `data/output/valid.jsonl`. Anything that still fails goes to `data/output/failed.jsonl` with the error, so bad data never slips in silently.

## Project structure

```
structured-extraction/
├── schemas.py          # Pydantic models (the data contract)
├── extractor.py        # Gemini call, validation, retry and repair logic
├── pipeline.py         # Reads raw files, runs extraction, saves results
├── data/
│   ├── raw/            # Input .txt files
│   └── output/         # valid.jsonl and failed.jsonl
├── tests/
│   └── test_schemas.py # Schema validation tests
└── requirements.txt
```

## Setup (Windows / PowerShell)

```powershell
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Get a free API key from [Google AI Studio](https://aistudio.google.com) and set it for the current terminal session:

```powershell
$env:GEMINI_API_KEY="your-key-here"
```

Never commit your API key to the repository.

## Usage

1. Put your messy text files (`.txt`) in `data/raw/`.
2. Run the pipeline:

```powershell
python pipeline.py
```

3. Check the results:

```powershell
Get-Content data\output\valid.jsonl
Get-Content data\output\failed.jsonl
```

## Tests

```powershell
python -m pytest tests/
```

The tests check the schema rules only, so they run offline and need no API key.

## Design notes

- **Validation checks format, not truth.** A wrong but well-formed value (such as a mis-read date) passes validation, so the prompt also states conventions explicitly (for example, `12/08/2026` is day-first) and tells the model never to invent values.
- **Empty input is rejected** before calling the model, so placeholder data cannot end up in the valid output.
- **Failed items are kept**, with their error, for manual review instead of being dropped.

## Extending the project

Swap the `Invoice` model in `schemas.py` for another schema, such as `Resume`, `SupportTicket` or `JobPosting`, and update the prompt. The rest of the pipeline stays the same.

Ideas for next steps: CSV export, MySQL storage, a Flask or FastAPI endpoint, and batch processing for large folders.

## Tech stack

Python, Google Gemini API (`google-genai`), Pydantic, pytest

## Author

Your Name
