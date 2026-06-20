"""Line language detection via fastText lid.176 model."""
import os
import fasttext

MODEL_PATH = os.path.join(os.path.dirname(__file__), "lid.176.bin")
THRESHOLD = 0.80  # FR-003: accept only when confidence >= 80%

_model = None  # loaded once per process (works with multiprocessing workers)

# fastText returns ISO codes; Names written for common cases.
_NAMES = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "mr": "Marathi", "hi": "Hindi", "ja": "Japanese", "zh": "Chinese",
    "ru": "Russian", "pt": "Portuguese", "it": "Italian", "ar": "Arabic",
}


def _load():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"fastText model missing: {MODEL_PATH} "
                "(download lid.176.bin, see CLAUDE.md)"
            )
        _model = fasttext.load_model(MODEL_PATH)
    return _model


def warmup():
    """Load the shared model once in the main thread before workers start."""
    _load()


def name(code: str) -> str:
    return _NAMES.get(code, code)


def detect(line: str):
    """Return (code, confidence). Confidence < THRESHOLD => caller marks Unknown.

    fastText cannot take newlines; caller passes a single stripped line.
    """
    labels, probs = _load().predict(line.replace("\n", " "), k=1)
    code = labels[0].replace("__label__", "")
    return code, float(probs[0])
