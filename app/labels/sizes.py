"""Label size utilities in 203 dpi dots."""

from typing import Dict

LABEL_SIZES_DOTS: Dict[str, Dict[str, int]] = {
    "2x1": {"width_dots": 203 * 2, "height_dots": 203 * 1},
    "4x6": {"width_dots": 203 * 4, "height_dots": 203 * 6},
}


def get_label_size_dots(size_key: str) -> Dict[str, int]:
    """Return width/height in dots for a given size key.

    Falls back to 4x6 if the key is unknown.
    """
    if size_key in LABEL_SIZES_DOTS:
        return LABEL_SIZES_DOTS[size_key]
    return LABEL_SIZES_DOTS["4x6"]
