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
        title_font = _load_font(28)
        text_font = _load_font(22)
        title_y = 8
        item_y = 40
        case_y = 66
        barcode_y = 88
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

    # Text
    draw.text((x_margin, title_y), title or "", fill=0, font=title_font)
    draw.text((x_margin, item_y), f"Item: {item_number or ''}", fill=0, font=text_font)
    draw.text((x_margin, case_y), f"Casepack: {casepack or ''}", fill=0, font=text_font)

    # Barcode
    if HAS_BARCODE and upc12 and upc12.isdigit() and len(upc12) == 12:
        try:
            try:
                cls = barcode.get_barcode_class("upc")
            except Exception:
                cls = barcode.get_barcode_class("upca")

            payload11 = upc12[:-1]
            bc = cls(payload11, writer=ImageWriter())
            bc_img = bc.render(writer_options={
                "module_width": 0.5,
                "module_height": barcode_height,
                "quiet_zone": 2.0,
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
            img.paste(bc_img.convert("L"), (x_margin, barcode_y))
        except Exception:
            logging.warning("Failed to render preview barcode", exc_info=True)
    else:
        draw.text((x_margin, barcode_y), "UPC preview unavailable", fill=0, font=_load_font(16))

    return img


def image_to_tk(img: Image.Image):
    from PIL import ImageTk
    return ImageTk.PhotoImage(img)
