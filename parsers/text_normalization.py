import math
import re
import unicodedata

NUMBER_PATTERN = re.compile(r"[+-]?\d+(?:[.,]\d+)?")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return (text.replace("\u00ad", "").replace("\u200b", "")
            .translate(str.maketrans({"–": "-", "—": "-", "−": "-"})))


def fold(text: str) -> str:
    return normalize_text(text).casefold().replace("\u0307", "").translate(
        str.maketrans("ıüöşçğ", "iuoscg")
    )


def number(token: str) -> float | None:
    if not NUMBER_PATTERN.fullmatch(token):
        return None
    value = float(token.replace(",", "."))
    return value if math.isfinite(value) else None


