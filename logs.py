"""Per-PDF logs, central error log, Detection summary."""
import os
from datetime import datetime

SEP = "-" * 52


def write_pdf_log(logs_dir, pdf_name, rows, doc_label):
    """rows: list of (page, line_no, lang_display, conf_pct, status)."""
    path = os.path.join(logs_dir, f"{pdf_name}_LanguageDetection.log")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"PDF Name: {pdf_name}.pdf\n")
        f.write(f"Processing Date: {datetime.now():%d-%b-%Y}\n\n")
        f.write(SEP + "\n")
        f.write("Page | Line No | Detected Language | Confidence | Status\n")
        f.write(SEP + "\n")
        for page, line_no, lang, conf, status in rows:
            f.write(f"{page:<4} | {line_no:<7} | {lang:<17} | "
                    f"{conf:>5} | {status}\n")
        f.write(SEP + "\n")
        f.write(f"Document Language: {doc_label}\n")
        f.write(SEP + "\n")


def append_error(error_path, pdf_name, etype, desc):
    """Central ErrorLog.txt — called only from the main process."""
    with open(error_path, "a", encoding="utf-8") as f:
        f.write(f"DateTime : {datetime.now():%d-%b-%Y %H:%M:%S}\n")
        f.write(f"PDF File : {pdf_name}\n")
        f.write(f"Error Type : {etype}\n")
        f.write(f"Description : {desc}\n")
        f.write(SEP + "\n")


def write_summary(path, total, success, failed):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Total PDFs Processed : {total}\n")
        f.write(f"Successfully Processed : {success}\n")
        f.write(f"Failed : {failed}\n")
