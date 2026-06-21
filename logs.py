"""Per-PDF logs, central error log, Detection summary."""
import os
from collections import Counter
from datetime import datetime

SEP = "-" * 52


def summarize(rows):
    acc = unk = ign = pages = 0
    langs = Counter()
    for page, _ln, lang, _conf, status in rows:
        pages = max(pages, page)
        if status == "Accepted":
            acc += 1
            langs[lang] += 1
        elif status == "Unknown":
            unk += 1
        else:
            ign += 1
    return {"pages": pages, "lines": acc + unk + ign, "accepted": acc,
            "unknown": unk, "ignored": ign, "langs": langs}


def write_pdf_log(logs_dir, pdf_name, rows, doc_label, verbose=False):
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
        if verbose:
            s = summarize(rows)
            f.write(f"Pages: {s['pages']} | Lines: {s['lines']} | "
                    f"Accepted: {s['accepted']} | Unknown: {s['unknown']} | "
                    f"Hyperlinks Ignored: {s['ignored']}\n")
            if s["langs"]:
                dist = ", ".join(f"{l} {n}" for l, n in s["langs"].most_common())
                f.write(f"Language Distribution: {dist}\n")
            f.write(SEP + "\n")
        f.write(f"Document Language: {doc_label}\n")
        f.write(SEP + "\n")


def append_error(error_path, pdf_name, etype, desc):
    with open(error_path, "a", encoding="utf-8") as f:
        f.write(f"DateTime : {datetime.now():%d-%b-%Y %H:%M:%S}\n")
        f.write(f"PDF File : {pdf_name}\n")
        f.write(f"Error Type : {etype}\n")
        f.write(f"Description : {desc}\n")
        f.write(SEP + "\n")


def write_summary(path, total, success, failed, details=None):
    """details (verbose only): the per-PDF result dicts for a breakdown."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Total PDFs Processed : {total}\n")
        f.write(f"Successfully Processed : {success}\n")
        f.write(f"Failed : {failed}\n")
        if not details:
            return
        lang_totals = Counter()
        for d in details:
            if d.get("stats"):
                lang_totals.update(d["stats"]["langs"])
        if lang_totals:
            f.write("\nAccepted lines by language:\n")
            for lang, n in lang_totals.most_common():
                f.write(f"  {lang} : {n}\n")
        f.write("\nPer PDF:\n")
        for d in details:
            if d["ok"]:
                s = d["stats"]
                f.write(f"  {d['name']} -> {d['label']} "
                        f"({s['accepted']} acc / {s['unknown']} unk / "
                        f"{s['ignored']} link, {s['pages']} pg, "
                        f"{d['secs']:.2f}s)\n")
            else:
                f.write(f"  {d['name']} -> FAILED ({d['etype']})\n")
