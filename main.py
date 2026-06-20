"""Main module for batch PDF language detection.

Graceful failure (FR-006): each PDF is isolated in try/except with a small
retry on transient I/O errors; a failure is logged to ErrorLog.txt and the
batch continues.
"""
import argparse
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import classify
import detect
import logs
from extract import pages_lines
from links import is_link_only, strip_links

# transient I/O errors are worth retrying; corrupted/empty PDFs are not.
_TRANSIENT = (PermissionError, BlockingIOError, TimeoutError)
_err_lock = threading.Lock()  # ErrorLog.txt is shared across threads


def _detect_pdf(pdf_path, output_dir, chunk_pages):
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    rows, valid = [], []
    for page, line_no, text in pages_lines(pdf_path, chunk_pages):
        if is_link_only(text):
            rows.append((page, line_no, "-", "-", "Ignored Hyperlink"))
            continue
        clean = strip_links(text)
        if not clean:
            continue
        code, conf = detect.detect(clean)
        pct = f"{conf * 100:.0f}%"
        if conf >= detect.THRESHOLD:
            rows.append((page, line_no, detect.name(code), pct, "Accepted"))
            valid.append(code)
        else:
            rows.append((page, line_no, detect.name(code), pct, "Unknown"))

    label, folder = classify.document_language(valid)
    logs.write_pdf_log(os.path.join(output_dir, "Logs"), name, rows, label)
    shutil.copy2(pdf_path, os.path.join(output_dir, folder))
    return label


def _process_one(pdf_path, output_dir, chunk_pages, attempts=3):
    """Worker task. Retries transient I/O, never raises — returns a result."""
    name = os.path.basename(pdf_path)
    last = None
    for i in range(1, attempts + 1):
        try:
            label = _detect_pdf(pdf_path, output_dir, chunk_pages)
            return {"name": name, "ok": True, "label": label}
        except _TRANSIENT as e:
            last = e
            time.sleep(0.5 * i)  # linear backoff, then retry
        except Exception as e:    # corrupted/empty/unsupported — don't retry
            return {"name": name, "ok": False,
                    "etype": type(e).__name__, "desc": str(e)}
    return {"name": name, "ok": False,
            "etype": type(last).__name__, "desc": f"{last} (after {attempts} tries)"}


def _setup_dirs(output_dir):
    for sub in (classify.ENGLISH, classify.NONENGLISH, classify.MIXED,
                classify.UNKNOWN, "Logs"):
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description="PDF language detection batch")
    ap.add_argument("input", help="PDF file or folder of PDFs")
    ap.add_argument("--output", default="Output")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    ap.add_argument("--chunk-pages", type=int, default=25,
                    help="pages held in memory at once per PDF")
    ap.add_argument("--serial", action="store_true",
                    help="single-threaded (easier debugging)")
    args = ap.parse_args()

    if os.path.isdir(args.input):
        pdfs = [os.path.join(args.input, f) for f in sorted(os.listdir(args.input))
                if f.lower().endswith(".pdf")]
    elif args.input.lower().endswith(".pdf"):
        pdfs = [args.input]
    else:
        sys.exit(f"Not a PDF or folder: {args.input}")
    if not pdfs:
        sys.exit(f"No PDFs found in: {args.input}")

    _setup_dirs(args.output)
    error_log = os.path.join(args.output, "ErrorLog.txt")
    open(error_log, "w").close()  # fresh run

    detect.warmup()  # load the shared model once, before threads start

    def run(p):
        return _process_one(p, args.output, args.chunk_pages)

    results = []
    if args.serial or len(pdfs) == 1:
        results = [run(p) for p in pdfs]
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(run, p) for p in pdfs]
            for fut in as_completed(futs):
                results.append(fut.result())

    success = 0
    for r in results:
        if r["ok"]:
            success += 1
            print(f"  {r['name']}: {r['label']}")
        else:
            with _err_lock:
                logs.append_error(error_log, r["name"], r["etype"], r["desc"])
            print(f"  {r['name']}: FAILED ({r['etype']})")

    failed = len(results) - success
    logs.write_summary(os.path.join(args.output, "SummaryReport.txt"),
                       len(results), success, failed)
    print(f"\nTotal {len(results)} | OK {success} | Failed {failed} "
          f"-> {args.output}/")


if __name__ == "__main__":
    main()
