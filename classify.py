"""Document-language rules + folder routing utility."""

# folder names per spec
ENGLISH, NONENGLISH, MIXED, UNKNOWN = (
    "English", "NonEnglish", "MixedLanguage", "Unknown",
)


def document_language(valid_codes):
    """Rules of document-language classification (only applied to sentences 
    that pass threshold of detection score>80%).

    valid_codes excludes Unknown lines and hyperlinks. Returns
    (label, folder) where label is what goes in the log/summary.
    """
    langs = set(valid_codes)
    if not langs:
        return "Unknown", UNKNOWN
    if langs == {"en"}:
        return "English", ENGLISH
    if len(langs) == 1:
        (only,) = langs
        return only, NONENGLISH        # single non-English language
    return "Mixed Language", MIXED      # 2+ distinct languages
