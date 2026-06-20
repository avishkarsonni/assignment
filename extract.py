"""PDF text extraction. PyMuPDF, page by page, line by line."""
import fitz


def pages_lines(pdf_path):
    """Yield (page_number, line_number, text) for every non-blank line.

    page_number and line_number start from 1. Raises on unreadable PDFs so the
    caller can log it and move on (FR-006).
    """
    doc = fitz.open(pdf_path)
    try:
        if doc.page_count == 0:
            raise ValueError("Empty PDF")
        for pno in range(doc.page_count):
            text = doc.load_page(pno).get_text()
            line_no = 0
            for raw in text.splitlines():
                if not raw.strip():
                    continue  # ignore blank / whitespace-only lines
                line_no += 1
                yield pno + 1, line_no, raw.strip()
    finally:
        doc.close()
