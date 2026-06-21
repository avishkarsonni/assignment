"""Error handling: transient-I/O retry + per-PDF
isolation so one bad file never stops the batch.

"""
import time
import traceback

# transient I/O errors are worth retrying; corrupted/empty PDFs are not.
TRANSIENT = (PermissionError, BlockingIOError, TimeoutError)


def run_isolated(task, name, verbose=False, attempts=3):
    """Run task() -> (label, stats); retry transient I/O, never raise.

    desc carries a full traceback when verbose.
    """
    last = None
    t0 = time.perf_counter()
    for i in range(1, attempts + 1):
        try:
            label, stats = task()
            return {"name": name, "ok": True, "label": label, "stats": stats,
                    "secs": time.perf_counter() - t0}
        except TRANSIENT as e:
            last = e
            time.sleep(0.5 * i)  # linear backoff: local locks clear fast
        except Exception as e:    # corrupted/empty/unsupported — don't retry
            desc = traceback.format_exc() if verbose else str(e)
            return {"name": name, "ok": False,
                    "etype": type(e).__name__, "desc": desc}
    return {"name": name, "ok": False, "etype": type(last).__name__,
            "desc": f"{last} (after {attempts} tries)"}
