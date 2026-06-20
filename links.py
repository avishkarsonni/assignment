"""Hyperlink detection / removal for language detection using Regex."""
import re

# http(s), www, mailto, ftp. ponytail: one regex covers all spec examples (common cases).
URL_RE = re.compile(
    r"\b(?:https?://|ftp://|www\.|mailto:)\S+",
    re.IGNORECASE,
)


def is_link_only(line: str) -> bool:
    """True if the whole line is just a hyperlink (nothing else to detect)."""
    return bool(line.strip()) and not URL_RE.sub("", line).strip()


def strip_links(line: str) -> str:
    """Remove inline hyperlinks, leaving the rest of the text for detection."""
    return URL_RE.sub(" ", line).strip()
