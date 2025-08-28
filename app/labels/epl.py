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


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Wrap text to multiple lines if needed."""
    if not text:
        return [""]
    if len(text) <= max_chars:
        return [text]
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line += (" " + word) if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines[:2]  # Max 2 lines


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
        title_font = 4  # Larger title font
        title_xy_mul = (1, 1)
        text_font = 3
        text_xy_mul = (1, 1)
        narrow = 3
        wide = 6
        barcode_height = 40
        title_y = 6
        item_y = 32
        case_y = 52
        barcode_y = 72
        x_margin = 20
        hri = "B"
    else:
        title_font = 4
        title_xy_mul = (1, 1)
        text_font = 3
        text_xy_mul = (1, 1)
        narrow = 3
        wide = 6
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
    
    # Wrap title to multiple lines if needed
    title_lines = wrap_text(safe_title, 36)

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

    # Title / fields (multi-line title support)
    for i, title_line in enumerate(title_lines):
        y_pos = title_y + (i * 24)  # Increased spacing between lines
        lines.append(_e(f"A{x_margin},{y_pos},0,{title_font},{title_xy_mul[0]},{title_xy_mul[1]},N,\"{title_line}\""))
    
    # Add separator line after title
    if title_lines and title_lines[0]:
        separator_y = title_y + (len(title_lines) * 24) + 8
        lines.append(_e(f"L{x_margin},{separator_y},{x_margin + 200},{separator_y},2"))
    
    # Adjust item position if title is multi-line
    item_y_adjusted = item_y + (len(title_lines) - 1) * 24
    if title_lines and title_lines[0]:
        item_y_adjusted += 16  # Extra space after separator
    lines.append(_e(f"A{x_margin},{item_y_adjusted},0,{text_font},{text_xy_mul[0]},{text_xy_mul[1]},N,\"{safe_item}\""))
    
    if safe_case:
        case_y_adjusted = case_y + (len(title_lines) - 1) * 24
        if title_lines and title_lines[0]:
            case_y_adjusted += 16  # Extra space after separator
        lines.append(_e(f"A{x_margin},{case_y_adjusted},0,{text_font},{text_xy_mul[0]},{text_xy_mul[1]},N,\"CS/PK: {safe_case}\""))

    # Code 128 barcode (only if UPC provided)
    if upc_payload and len(upc_payload) >= 11:
        barcode_y_adjusted = barcode_y + (len(title_lines) - 1) * 24
        if title_lines and title_lines[0]:
            barcode_y_adjusted += 16  # Extra space after separator
        lines.append(_e(f"B{x_margin},{barcode_y_adjusted},0,1,{narrow},{wide},{barcode_height},{hri},\"{upc_payload}\""))

    if copies and copies > 1:
        lines.append(_e(f"P{copies}"))
    else:
        lines.append(_e("P1"))

    data = "".join(lines)
    return data.encode("ascii", errors="ignore")
