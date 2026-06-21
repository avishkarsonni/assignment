# PDF Language Detector

Sorts a batch of PDFs into language folders using fastText line-by-line language identification.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (or `pip` if you prefer)
- ~200 MB disk space for the fastText model

## Setup

```bash
# 1. Create virtual environment
uv venv --python 3.12 .venv

# 2. Install dependencies
uv pip install --python .venv -r requirements.txt

# 3. Download the fastText language-identification model (126 MB)
curl -fSL -o lid.176.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
```

That's it. The model is loaded once at startup and shared across all worker threads.

## Run

```bash
# Single PDF
.venv/bin/python main.py document.pdf

# Entire folder
.venv/bin/python main.py ./pdfs_to_sort/

# Custom output directory
.venv/bin/python main.py ./pdfs_to_sort/ --output SortedOutput/

# Adjust workers (default: min(8, cpu_count))
.venv/bin/python main.py ./pdfs_to_sort/ --workers 4

# Adjust chunk size (pages held in memory per PDF, default: 25)
.venv/bin/python main.py ./pdfs_to_sort/ --chunk-pages 50

# Single-threaded (easier to debug)
.venv/bin/python main.py ./pdfs_to_sort/ --serial

# Verbose: detailed per-PDF logs and summary breakdown
.venv/bin/python main.py ./pdfs_to_sort/ -v
```

## Output

```
Output/
├── English/          # PDFs where every detected line is English
├── NonEnglish/        # PDFs in a single non-English language
├── MixedLanguage/     # PDFs with 2+ distinct languages detected
├── Unknown/          # PDFs with no confident detections
├── Logs/             # Per-PDF language detection logs
├── ErrorLog.txt      # Failed PDFs with error details
└── SummaryReport.txt # Batch-level totals
```

## Project Structure

```
.
├── main.py      # CLI entry point, thread pool, retry logic
├── extract.py  # PyMuPDF page-chunked text extraction
├── detect.py   # fastText model wrapper, 80% confidence threshold
├── classify.py # Document language rules → output folder
├── links.py    # URL/hyperlink detection and stripping
├── logs.py     # Per-PDF logs, error log, summary report
└── requirements.txt
```

## Dependencies

| Package | Why |
|---------|-----|
| PyMuPDF >= 1.24 | PDF text extraction |
| fasttext-wheel >= 0.9.2 | Language identification |
| numpy < 2 | fasttext-wheel dependency; numpy 2.x breaks it |

## Verifying the Setup

```bash
# Sanity-check the classification rules
.venv/bin/python classify.py
# Expected output: classify rules OK

# Run on a known PDF
.venv/bin/python main.py sample.pdf -v
```

## Troubleshooting

**`fastText model missing`** — `lid.176.bin` wasn't downloaded or is in the wrong directory. It must be in the same folder as `detect.py`.

**`AttributeError` on `np.array(copy=False)`** — numpy 2.x is installed. Reinstall with `numpy<2` from requirements.txt.

**High memory usage** — Reduce `--chunk-pages` (default 25). Smaller chunks = lower peak memory per PDF.

**Slow on large PDFs** — Use `--workers` to increase parallelism. Threads share the model, so additional workers add minimal memory overhead (~1-2 MB each).
