# Dagsplan Importer

This repository contains a small command-line utility, `dagsplan_importer.py`, that can:

1. Perform OCR on a scanned dagsplan (daily schedule) image or PDF using Tesseract.
2. Apply lightweight heuristics to extract dated time slots and descriptions from the OCR text.
3. Export the events to an `.ics` file that can be imported into the calendar provider of your choice (Google Calendar, Outlook, Apple Calendar, etc.).

## Requirements

* Python 3.9+
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and available on the system `PATH`.
* Python packages: `pytesseract`, `Pillow`, and optionally `pdf2image` (for PDF support).

## Usage

```bash
python dagsplan_importer.py <path-to-dagsplan-image-or-pdf> \
    --timezone Europe/Oslo \
    --date 2024-03-12 \
    --calendar google \
    --output dagsplan.ics
```

* `--tesseract-lang` defaults to `nor` (Norwegian). Change if your dagsplan uses a different language.
* If the OCR text does not contain a date, provide one with `--date`.
* Choosing `--calendar google` or `--calendar outlook` produces an `.ics` file and prints import instructions specific to that provider.
* The resulting `.ics` file can be imported into Google Calendar via **Settings → Import & Export**, or into Outlook via **File → Open & Export → Import/Export**.
* Lines that do not match a time slot are printed as free-form notes after the calendar export completes.
