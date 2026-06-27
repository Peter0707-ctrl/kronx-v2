from langdetect import detect
from typing import Optional

def detect_language(text: str) -> str:
    """
    Detect if text is Swahili or English.
    Returns 'sw' or 'en'.
    """
    try:
        lang = detect(text)
        if lang == 'sw':
            return 'sw'
        return 'en'
    except:
        return 'en'

def format_currency(amount: float, currency: str = "TZS") -> str:
    """
    Format currency for Tanzanian context.
    """
    if currency == "TZS":
        return f"TZS {amount:,.0f}"
    return f"{currency} {amount:,.2f}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text for titles and previews.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def clean_message(text: str) -> str:
    """
    Clean and normalize a message before processing.
    """
    return text.strip()

def get_mode_context(mode: str) -> dict:
    """
    Return context information for each Kronx mode.
    """
    modes = {
        "Friend": {
            "sw": "Rafiki",
            "en": "Friend",
            "max_tokens": 512,
            "temperature": 0.8,
        },
        "Teacher": {
            "sw": "Mwalimu",
            "en": "Teacher",
            "max_tokens": 1024,
            "temperature": 0.5,
        },
        "Business": {
            "sw": "Biashara",
            "en": "Business",
            "max_tokens": 1024,
            "temperature": 0.4,
        },
        "Research": {
            "sw": "Utafiti",
            "en": "Research",
            "max_tokens": 2048,
            "temperature": 0.3,
        },
        "Quick": {
            "sw": "Haraka",
            "en": "Quick",
            "max_tokens": 256,
            "temperature": 0.7,
        },
    }
    return modes.get(mode, modes["Friend"])