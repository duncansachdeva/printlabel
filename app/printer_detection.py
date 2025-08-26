"""Utilities to guess printer language (ZPL/EPL) by printer name."""
from typing import Literal

PrinterLanguage = Literal["ZPL", "EPL"]


def guess_printer_language(printer_name: str) -> PrinterLanguage:
    """Guess ZPL or EPL based on common Zebra model names.

    Defaults to ZPL if unknown.
    """
    if not printer_name:
        return "ZPL"

    lower_name = printer_name.lower()

    # Very common EPL models
    if "lp2844" in lower_name or "lp 2844" in lower_name or "2844" in lower_name:
        return "EPL"

    # Common ZPL models
    if "zm" in lower_name or "zpl" in lower_name or "zebra z" in lower_name:
        return "ZPL"

    return "ZPL"
