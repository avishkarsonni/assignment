"""PDF text extraction (FR-002). PyMuPDF, page by page, line by line.

Pages are read in chunks of `chunk_pages`: at most that many page-texts are
held in memory at once, so peak memory is bound by chunk size, not PDF length.
"""

import fitz


def pages_lines(pdf_path, chunk_pages=25):
    """Yield (page_number, line_number, text) for every non-blank line.

    page_number and line_number start from 1. Raises on unreadable PDFs so the
    caller can log it and move on (FR-006).
    """
    doc = fitz.open(pdf_path)
    try:
        n = doc.page_count
        if n == 0:
            raise ValueError("Empty PDF")
        for start in range(0, n, chunk_pages):
            # hold one chunk of page-texts, then release before the next chunk
            chunk = [(p + 1, doc.load_page(p).get_text())
                     for p in range(start, min(start + chunk_pages, n))]
            for page_no, text in chunk:
                line_no = 0
                for raw in text.splitlines():
                    if not raw.strip():
                        continue  # ignore blank / whitespace-only lines
                    line_no += 1
                    yield page_no, line_no, raw.strip()
    finally:
        doc.close()
