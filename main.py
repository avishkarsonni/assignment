"""Main module for batch PDF language detection.

Graceful failure: failure is logged to ErrorLog.txt and the
batch continues.
"""
import argparse
import json
import os
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace

import classify
import detect
import errors
import logs
from extract import pages_lines
from links import is_link_only, strip_links

_err_lock = threading.Lock()  # ErrorLog.txt is shared across threads


def _detect_pdf(pdf_path, output_dir, chunk_pages, verbose=False):
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
    logs.write_pdf_log(os.path.join(output_dir, "Logs"), name, rows, label,
                       verbose=verbose)
    shutil.copy2(pdf_path, os.path.join(output_dir, folder))
    return label, logs.summarize(rows)


def _setup_dirs(output_dir):
    for sub in (classify.ENGLISH, classify.NONENGLISH, classify.MIXED,
                classify.UNKNOWN, "Logs"):
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)


def main():
    # SRS: fully JSON-configured. The only CLI arg is which config file to read.
    ap = argparse.ArgumentParser(description="PDF language detection (JSON-configured)")
    ap.add_argument("config", nargs="?", default="config.json",
                    help="JSON config file (default: config.json)")
    cfg_path = ap.parse_args().config
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        sys.exit(f"Config not found: {cfg_path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Bad JSON in {cfg_path}: {e}")
    if "input" not in cfg:
        sys.exit(f"Config {cfg_path} missing required key: input")

    # defaults for everything optional; config.json overrides.
    args = SimpleNamespace(**{
        "output": "Output", "workers": min(8, os.cpu_count() or 4),
        "chunk_pages": 25, "serial": False, "verbose": False, **cfg})

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
        return errors.run_isolated(
            lambda: _detect_pdf(p, args.output, args.chunk_pages, args.verbose),
            os.path.basename(p), verbose=args.verbose)

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
            if args.verbose:
                s = r["stats"]
                print(f"  {r['name']}: {r['label']} "
                      f"({s['accepted']} acc / {s['unknown']} unk / "
                      f"{s['ignored']} link, {s['pages']} pg, {r['secs']:.2f}s)")
            else:
                print(f"  {r['name']}: {r['label']}")
        else:
            with _err_lock:
                logs.append_error(error_log, r["name"], r["etype"], r["desc"])
            print(f"  {r['name']}: FAILED ({r['etype']})")

    failed = len(results) - success
    logs.write_summary(os.path.join(args.output, "SummaryReport.txt"),
                       len(results), success, failed,
                       details=results if args.verbose else None)
    print(f"\nTotal {len(results)} | OK {success} | Failed {failed} "
          f"-> {args.output}/")


if __name__ == "__main__":
    main()
