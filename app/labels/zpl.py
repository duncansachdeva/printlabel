"""ZPL label template generation."""
from typing import Dict

from app.labels.sizes import get_label_size_dots


def truncate_text(text: str, max_chars: int) -> str:
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def build_zpl_label(
    *,
    size_key: str,
    item_number: str,
    upc12: str,
    title: str,
    casepack: str,
    copies: int,
) -> bytes:
    """Build a ZPL label for the given fields and size.

    Uses a simple layout tuned for 203 dpi printers.
    """
    dims = get_label_size_dots(size_key)
    width = dims["width_dots"]
    height = dims["height_dots"]

    # Basic typography per size
    if size_key == "2x1":
        title_font = (30, 30)
        text_font = (24, 24)
        barcode_height = 80
        title_y = 10
        item_y = 50
        case_y = 80
        barcode_y = 110
    else:  # 4x6 default
        title_font = (48, 48)
        text_font = (36, 36)
        barcode_height = 300
        title_y = 40
        item_y = 110
        case_y = 160
        barcode_y = 220

    safe_title = truncate_text(title or "", 36)
    safe_item = truncate_text(item_number or "", 36)
    safe_case = truncate_text(casepack or "", 36)

    zpl = []
    zpl.append("^XA")
    zpl.append(f"^PW{width}")
    zpl.append(f"^LL{height}")
    zpl.append("^LH0,0")
    zpl.append("^CI28")

    # Title
    zpl.append(f"^FO20,{title_y}^A0N,{title_font[0]},{title_font[1]}^FD{safe_title}^FS")
    # Item
    zpl.append(f"^FO20,{item_y}^A0N,{text_font[0]},{text_font[1]}^FDItem: {safe_item}^FS")
    # Casepack
    zpl.append(f"^FO20,{case_y}^A0N,{text_font[0]},{text_font[1]}^FDCasepack: {safe_case}^FS")

    # Barcode defaults and UPC-A (^BU)
    zpl.append("^BY2,2,10")
    zpl.append(f"^FO20,{barcode_y}^BUN,{barcode_height},Y,N^FD{upc12}^FS")

    if copies and copies > 1:
        zpl.append(f"^PQ{copies}")

    zpl.append("^XZ")

    data = "".join(zpl)
    return data.encode("utf-8")
