"""Validation helpers."""
from typing import Optional


def compute_upc_check_digit(upc11: str) -> str:
    """Compute the UPC-A 12th check digit for 11-digit payload."""
    digits = [int(c) for c in upc11]
    odd_sum = sum(digits[0::2])
    even_sum = sum(digits[1::2])
    total = odd_sum * 3 + even_sum
    check = (10 - (total % 10)) % 10
    return str(check)


def ensure_upc12(upc: str) -> Optional[str]:
    """Return a 12-digit UPC-A.

    - If input is 11 digits, appends the correct check digit.
    - If input is 12 digits and has a correct check digit, returns as-is.
    - Otherwise returns None.
    """
    if upc is None:
        return None
    clean = "".join([c for c in upc if c.isdigit()])
    if len(clean) == 11:
        return clean + compute_upc_check_digit(clean)
    if len(clean) == 12:
        payload = clean[:11]
        expected = compute_upc_check_digit(payload)
        if clean[-1] == expected:
            return clean
        return None
    return None


def sanitize_text(value: str, max_len: int = 64) -> str:
    """Limit to ASCII-friendly characters and truncate."""
    if value is None:
        return ""
    ascii_only = value.encode("ascii", errors="ignore").decode("ascii")
    if len(ascii_only) <= max_len:
        return ascii_only
    return ascii_only[: max_len]
