"""Optional on-demand English news headline translation.

Uses the free public MyMemory endpoint with no API key. This is not a guaranteed
real-time translation service. Only the headline (never price data) is sent.
"""
import json
import re
import urllib.parse
import urllib.request

ENDPOINT = "https://api.mymemory.translated.net/get"

def needs_translation(title: str) -> bool:
    """Skip Chinese-language headlines and non-alphabetic strings."""
    return bool(re.search(r"[A-Za-z]", title)) and not bool(re.search(r"[\u3400-\u9fff]", title))

def translate_headline(title: str, timeout: float = 5.0) -> tuple[str, bool]:
    """Return (translated/original title, translation_succeeded).

    Call only with explicit user opt-in. Never hide the original English title.
    """
    title = str(title).strip()
    if not title or not needs_translation(title):
        return title, False
    # Conservative cap for the free endpoint and to avoid unusually long requests.
    if len(title) > 450:
        return title, False
    params = urllib.parse.urlencode({"q": title, "langpair": "en|zh-TW"})
    req = urllib.request.Request(
        ENDPOINT + "?" + params,
        headers={"User-Agent": "PRBM/1.0 (financial news headline accessibility)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read(30_000).decode("utf-8"))
        status = payload.get("responseStatus")
        result = payload.get("responseData", {})
        translated = str(result.get("translatedText") or "").strip()
        if int(status or 0) != 200 or not translated:
            return title, False
        if translated.lower() == title.lower():
            return title, False
        # Never display errors from a third-party response as a translation.
        if "QUERY LENGTH LIMIT" in translated.upper() or "MYMEMORY WARNING" in translated.upper():
            return title, False
        return translated, True
    except (ValueError, TypeError, OSError, UnicodeError):
        return title, False
