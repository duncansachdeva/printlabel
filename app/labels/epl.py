"""EPL label template generation."""
from typing import Dict

from app.labels.sizes import get_label_size_dots
from app.utils.validation import compute_upc_check_digit


def _e(line: str) -> str:
    return line + "\r\n"


def truncate_text(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def build_epl_label(
    *,
    size_key: str,
    item_number: str,
    upc12: str,
    title: str,
    casepack: str,
    copies: int,
) -> bytes:
    """Build an EPL label for the given fields and size."""
    dims = get_label_size_dots(size_key)
    width = dims["width_dots"]
    height = dims["height_dots"]

    if size_key == "2x1":
        title_font = 3
        title_xy_mul = (1, 1)
        text_font = 3
        text_xy_mul = (1, 1)
        narrow = 2
        wide = 4
        barcode_height = 60
        title_y = 8
        item_y = 40
        case_y = 66
        barcode_y = 88
        x_margin = 20
        hri = "B"
    else:
        title_font = 4
        title_xy_mul = (1, 1)
        text_font = 3
        text_xy_mul = (1, 1)
        narrow = 2
        wide = 4
        barcode_height = 280
        title_y = 40
        item_y = 110
        case_y = 160
        barcode_y = 210
        x_margin = 40
        hri = "B"

    # Truncate/sanitize text for EPL ASCII
    safe_title = truncate_text(title or "", 36)
    safe_item = truncate_text(item_number or "", 36)
    safe_case = truncate_text(casepack or "", 36)

    # Ensure 12-digit UPC-A data (compute if only 11 provided)
    digits = "".join(ch for ch in (upc12 or "") if ch.isdigit())
    if len(digits) >= 12:
        upc_payload = digits[:12]
    elif len(digits) == 11:
        upc_payload = digits + compute_upc_check_digit(digits)
    else:
        upc_payload = digits

    lines = []
    lines.append(_e("N"))
    lines.append(_e(f"q{width}"))
    lines.append(_e(f"Q{height},24"))

    # Title / fields
    lines.append(_e(f"A{x_margin},{title_y},0,{title_font},{title_xy_mul[0]},{title_xy_mul[1]},N,\"{safe_title}\""))
    lines.append(_e(f"A{x_margin},{item_y},0,{text_font},{text_xy_mul[0]},{text_xy_mul[1]},N,\"Item: {safe_item}\""))
    lines.append(_e(f"A{x_margin},{case_y},0,{text_font},{text_xy_mul[0]},{text_xy_mul[1]},N,\"Casepack: {safe_case}\""))

    # UPC-A barcode: 'U' type, HRI below, no quotes in data
    lines.append(_e(f"B{x_margin},{barcode_y},0,U,{narrow},{wide},{barcode_height},{hri},{upc_payload}"))

    if copies and copies > 1:
        lines.append(_e(f"P{copies}"))
    else:
        lines.append(_e("P1"))

    data = "".join(lines)
    return data.encode("ascii", errors="ignore")
