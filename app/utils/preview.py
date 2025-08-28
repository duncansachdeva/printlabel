"""Preview rendering utilities using Pillow.

Renders a raster preview of the label at 203 dpi for display in Tkinter.
"""
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
import io
import logging

try:
    import barcode  # type: ignore
    from barcode.writer import ImageWriter  # type: ignore
    HAS_BARCODE = True
except Exception:
    HAS_BARCODE = False


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


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


def render_label_preview(
    *,
    width_dots: int,
    height_dots: int,
    title: str,
    item_number: str,
    casepack: str,
    upc12: str,
) -> Image.Image:
    img = Image.new("L", (width_dots, height_dots), color=255)
    draw = ImageDraw.Draw(img)

    # Layout heuristics similar to builders
    if height_dots <= 203:  # ~2x1
        title_font = _load_font(32)  # Larger title
        text_font = _load_font(22)
        title_y = 10
        item_y = 44
        case_y = 70
        barcode_y = 92
        x_margin = 20
        barcode_height = 60
        font_size = 14
    else:
        title_font = _load_font(44)
        text_font = _load_font(32)
        title_y = 40
        item_y = 110
        case_y = 160
        barcode_y = 210
        x_margin = 40
        barcode_height = 280
        font_size = 20

    # Text with multi-line title support
    title_lines = wrap_text(title or "", 36)
    for i, title_line in enumerate(title_lines):
        y_pos = title_y + (i * 24)
        draw.text((x_margin, y_pos), title_line, fill=0, font=title_font)
    
    # Add separator line after title
    if title_lines and title_lines[0]:
        separator_y = title_y + (len(title_lines) * 24) + 8
        draw.line([(x_margin, separator_y), (x_margin + 200, separator_y)], fill=0, width=2)
    
    # Adjust positions for multi-line title
    item_y_adjusted = item_y + (len(title_lines) - 1) * 24
    if title_lines and title_lines[0]:
        item_y_adjusted += 16  # Extra space after separator
    draw.text((x_margin, item_y_adjusted), item_number or "", fill=0, font=text_font)
    
    if casepack:
        case_y_adjusted = case_y + (len(title_lines) - 1) * 24
        if title_lines and title_lines[0]:
            case_y_adjusted += 16  # Extra space after separator
        draw.text((x_margin, case_y_adjusted), f"CS/PK: {casepack}", fill=0, font=text_font)

    # Barcode (only if UPC provided)
    if HAS_BARCODE and upc12 and upc12.isdigit() and len(upc12) == 12:
        try:
            try:
                cls = barcode.get_barcode_class("upc")
            except Exception:
                cls = barcode.get_barcode_class("upca")

            payload11 = upc12[:-1]
            bc = cls(payload11, writer=ImageWriter())
            bc_img = bc.render(writer_options={
                "module_width": 0.8,
                "module_height": barcode_height,
                "quiet_zone": 1.0,
                "write_text": True,
                "font_size": font_size,
                "text_distance": 2,
            })
            # Scale barcode to fit within the label width minus margins (only downscale)
            max_w = max(10, width_dots - (x_margin * 2))
            if bc_img.width > max_w:
                scale = max_w / bc_img.width
                new_size = (int(bc_img.width * scale), int(bc_img.height * scale))
                bc_img = bc_img.resize(new_size)
            barcode_y_adjusted = barcode_y + (len(title_lines) - 1) * 24
            if title_lines and title_lines[0]:
                barcode_y_adjusted += 16  # Extra space after separator
            img.paste(bc_img.convert("L"), (x_margin, barcode_y_adjusted))
        except Exception:
            logging.warning("Failed to render preview barcode", exc_info=True)
    else:
        if upc12 and upc12.strip():  # Only show message if UPC was entered but invalid
            barcode_y_adjusted = barcode_y + (len(title_lines) - 1) * 24
            if title_lines and title_lines[0]:
                barcode_y_adjusted += 16  # Extra space after separator
            draw.text((x_margin, barcode_y_adjusted), "UPC preview unavailable", fill=0, font=_load_font(16))

    return img


def image_to_tk(img: Image.Image):
    from PIL import ImageTk
    return ImageTk.PhotoImage(img)
