"""Settings management for label configuration."""
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class LabelSettings:
    """Settings for a specific label size and printer combination."""
    
    # Font Settings
    title_font: int = 4  # EPL font number (1-5)
    text_font: int = 3   # EPL font number for item/casepack
    title_xy_mul_x: int = 1  # Font compression X
    title_xy_mul_y: int = 2  # Font compression Y (higher = narrower)
    
    # Layout & Spacing
    x_margin: int = 20   # Left margin in dots
    title_y: int = 6     # Title Y position
    item_y: int = 32     # Item number Y position
    case_y: int = 52     # Casepack Y position
    barcode_y: int = 72  # Barcode Y position
    line_spacing: int = 24  # Spacing between title lines
    
    # Text Limits
    title_max_chars: int = 24
    item_max_chars: int = 36
    case_max_chars: int = 36
    max_title_lines: int = 2
    
    # Visual Elements
    show_separator: bool = True
    separator_width: int = 200
    separator_thickness: int = 2
    
    # Barcode Settings
    barcode_height: int = 40
    barcode_narrow: int = 3
    barcode_wide: int = 6
    barcode_hri: str = "B"  # Human readable text position
    
    # Label Orientation
    orientation: str = "normal"  # normal, rotated90, rotated180, rotated270
    
    # Preview Settings
    preview_title_font_size: int = 24
    preview_text_font_size: int = 22


class SettingsManager:
    """Manages label settings with per-printer and per-label-size storage."""
    
    def __init__(self, db_path: str = "label_settings.json"):
        self.db_path = db_path
        self.settings_cache: Dict[str, LabelSettings] = {}
        self._load_settings()
    
    def _get_settings_key(self, printer_name: str, label_size: str) -> str:
        """Generate a unique key for printer + label size combination."""
        return f"{printer_name}_{label_size}"
    
    def _get_default_settings(self, label_size: str) -> LabelSettings:
        """Get default settings for a label size."""
        if label_size == "2x1":
            return LabelSettings(
                title_font=4,
                text_font=3,
                title_xy_mul_x=1,
                title_xy_mul_y=2,
                x_margin=20,
                title_y=6,
                item_y=32,
                case_y=52,
                barcode_y=72,
                line_spacing=24,
                title_max_chars=24,
                item_max_chars=36,
                case_max_chars=36,
                max_title_lines=2,
                show_separator=True,
                separator_width=200,
                separator_thickness=2,
                barcode_height=40,
                barcode_narrow=3,
                barcode_wide=6,
                barcode_hri="B",
                orientation="normal",
                preview_title_font_size=24,
                preview_text_font_size=22
            )
        else:  # 4x6
            return LabelSettings(
                title_font=4,
                text_font=3,
                title_xy_mul_x=1,
                title_xy_mul_y=3,
                x_margin=40,
                title_y=40,
                item_y=110,
                case_y=160,
                barcode_y=210,
                line_spacing=24,
                title_max_chars=24,
                item_max_chars=36,
                case_max_chars=36,
                max_title_lines=2,
                show_separator=True,
                separator_width=200,
                separator_thickness=2,
                barcode_height=280,
                barcode_narrow=3,
                barcode_wide=6,
                barcode_hri="B",
                orientation="normal",
                preview_title_font_size=28,
                preview_text_font_size=32
            )
    
    def get_settings(self, printer_name: str, label_size: str) -> LabelSettings:
        """Get settings for a specific printer and label size."""
        key = self._get_settings_key(printer_name, label_size)
        
        if key not in self.settings_cache:
            # Load from file or use defaults
            self.settings_cache[key] = self._load_printer_settings(printer_name, label_size)
        
        return self.settings_cache[key]
    
    def save_settings(self, printer_name: str, label_size: str, settings: LabelSettings) -> None:
        """Save settings for a specific printer and label size."""
        key = self._get_settings_key(printer_name, label_size)
        self.settings_cache[key] = settings
        self._save_all_settings()
    
    def reset_to_default(self, printer_name: str, label_size: str) -> LabelSettings:
        """Reset settings to default for a specific printer and label size."""
        default_settings = self._get_default_settings(label_size)
        self.save_settings(printer_name, label_size, default_settings)
        return default_settings
    
    def _load_settings(self) -> None:
        """Load all settings from file."""
        if not os.path.exists(self.db_path):
            return
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for key, settings_dict in data.items():
                try:
                    settings = LabelSettings(**settings_dict)
                    self.settings_cache[key] = settings
                except Exception as e:
                    logger.warning(f"Failed to load settings for {key}: {e}")
        except Exception as e:
            logger.error(f"Failed to load settings file: {e}")
    
    def _load_printer_settings(self, printer_name: str, label_size: str) -> LabelSettings:
        """Load settings for a specific printer from file or return defaults."""
        if not os.path.exists(self.db_path):
            return self._get_default_settings(label_size)
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            key = self._get_settings_key(printer_name, label_size)
            if key in data:
                return LabelSettings(**data[key])
        except Exception as e:
            logger.error(f"Failed to load printer settings: {e}")
        
        return self._get_default_settings(label_size)
    
    def _save_all_settings(self) -> None:
        """Save all settings to file."""
        try:
            data = {}
            for key, settings in self.settings_cache.items():
                data[key] = asdict(settings)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def get_all_printer_names(self) -> list[str]:
        """Get list of all printer names that have saved settings."""
        printer_names = set()
        for key in self.settings_cache.keys():
            if '_' in key:
                printer_name = key.rsplit('_', 1)[0]
                printer_names.add(printer_name)
        return sorted(list(printer_names))
