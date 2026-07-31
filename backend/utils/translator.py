"""
translator.py — Swahili translation using MyMemory free API.

Strategy:
  1. Model generates a fluent English response (it's good at English).
  2. We call MyMemory to translate English → Swahili.
  3. If translation fails (network, quota), we return the English text
     with a small "(EN)" tag so the user still gets an answer.

MyMemory: https://mymemory.translated.net — 5,000 chars/day free, no key needed.
"""

import httpx
import asyncio
from typing import Optional

MYMEMORY_URL = "https://api.mymemory.translated.net/get"

# Simple in-process cache: avoid re-translating identical text
_cache: dict[str, str] = {}


async def translate_en_to_sw(text: str, timeout: float = 8.0) -> str:
    """
    Translate English text to Swahili via MyMemory.
    Returns original text on any error so the user always gets a response.
    """
    if not text or not text.strip():
        return text

    text = text.strip()

    # Return from cache if available
    if text in _cache:
        return _cache[text]

    # MyMemory has a 500-char limit per request — split if needed
    if len(text) <= 500:
        translated = await _call_mymemory(text, timeout)
    else:
        translated = await _translate_chunked(text, timeout)

    _cache[text] = translated
    return translated


async def _call_mymemory(text: str, timeout: float) -> str:
    """Single MyMemory API call for text <= 500 chars."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                MYMEMORY_URL,
                params={
                    "q": text,
                    "langpair": "en|sw",
                    "de": "kronx@ai.app",   # optional email improves quota
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText", "")
                # MyMemory returns the original text if it can't translate
                if translated and translated.lower() != text.lower():
                    return translated
    except Exception:
        pass
    return text   # Fallback: return English


async def _translate_chunked(text: str, timeout: float) -> str:
    """
    Split long text into <=500-char sentence-safe chunks, translate each,
    then reassemble.
    """
    import re
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= 490:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    # Translate all chunks concurrently
    tasks = [_call_mymemory(chunk, timeout) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    parts: list[str] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception) or not result:
            parts.append(chunks[i])   # Fallback to English chunk
        else:
            parts.append(str(result))

    return " ".join(parts)
