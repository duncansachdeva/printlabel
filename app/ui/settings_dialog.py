"""Settings dialog for label configuration."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import logging

from app.utils.settings import SettingsManager, LabelSettings
from app.utils.preview import render_label_preview, image_to_tk
from app.labels.sizes import get_label_size_dots

logger = logging.getLogger(__name__)


class SettingsDialog:
    """Dialog for configuring label settings with real-time preview."""
    
    def __init__(self, parent: tk.Tk, settings_manager: SettingsManager, 
                 printer_name: str, label_size: str, 
                 on_settings_changed: Optional[Callable] = None):
        self.parent = parent
        self.settings_manager = settings_manager
        self.printer_name = printer_name
        self.label_size = label_size
        self.on_settings_changed = on_settings_changed
        
        # Get current settings
        self.current_settings = settings_manager.get_settings(printer_name, label_size)
        self.original_settings = self.current_settings
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Label Settings - {printer_name} ({label_size})")
        self.dialog.geometry("800x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"800x700+{x}+{y}")
        
        self._create_widgets()
        self._update_preview()
    
    def _create_widgets(self):
        """Create the settings dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Label Configuration Settings", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Left panel - Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        # Right panel - Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="10")
        preview_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        # Create settings widgets
        self._create_settings_widgets(settings_frame)
        
        # Create preview widget
        self._create_preview_widget(preview_frame)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Reset to Default", 
                  command=self._reset_to_default).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", 
                  command=self._cancel).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Apply", 
                  command=self._apply).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="OK", 
                  command=self._ok).pack(side="left")
    
    def _create_settings_widgets(self, parent):
        """Create the settings control widgets."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Font Settings Section
        font_frame = ttk.LabelFrame(scrollable_frame, text="Font Settings", padding="5")
        font_frame.pack(fill="x", pady=(0, 10))
        
        # Title Font
        ttk.Label(font_frame, text="Title Font (EPL 1-5):").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.title_font_var = tk.IntVar(value=self.current_settings.title_font)
        title_font_spin = ttk.Spinbox(font_frame, from_=1, to=5, width=10, 
                                     textvariable=self.title_font_var,
                                     command=self._on_setting_changed)
        title_font_spin.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        # Text Font
        ttk.Label(font_frame, text="Text Font (EPL 1-5):").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.text_font_var = tk.IntVar(value=self.current_settings.text_font)
        text_font_spin = ttk.Spinbox(font_frame, from_=1, to=5, width=10,
                                    textvariable=self.text_font_var,
                                    command=self._on_setting_changed)
        text_font_spin.grid(row=1, column=1, sticky="w", padx=(0, 10))
        
        # Font Compression
        ttk.Label(font_frame, text="Title Font Compression Y:").grid(row=2, column=0, sticky="w", padx=(0, 5))
        self.title_xy_mul_y_var = tk.IntVar(value=self.current_settings.title_xy_mul_y)
        title_comp_spin = ttk.Spinbox(font_frame, from_=1, to=5, width=10,
                                     textvariable=self.title_xy_mul_y_var,
                                     command=self._on_setting_changed)
        title_comp_spin.grid(row=2, column=1, sticky="w", padx=(0, 10))
        
        # Layout Settings Section
        layout_frame = ttk.LabelFrame(scrollable_frame, text="Layout & Spacing", padding="5")
        layout_frame.pack(fill="x", pady=(0, 10))
        
        # Margins and Positions
        positions = [
            ("Left Margin (dots):", "x_margin_var", self.current_settings.x_margin),
            ("Title Y Position:", "title_y_var", self.current_settings.title_y),
            ("Item Y Position:", "item_y_var", self.current_settings.item_y),
            ("Case Y Position:", "case_y_var", self.current_settings.case_y),
            ("Barcode Y Position:", "barcode_y_var", self.current_settings.barcode_y),
            ("Line Spacing:", "line_spacing_var", self.current_settings.line_spacing),
        ]
        
        for i, (label, var_name, value) in enumerate(positions):
            ttk.Label(layout_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 5))
            var = tk.IntVar(value=value)
            setattr(self, var_name, var)
            spin = ttk.Spinbox(layout_frame, from_=0, to=1000, width=10,
                              textvariable=var, command=self._on_setting_changed)
            spin.grid(row=i, column=1, sticky="w", padx=(0, 10))
        
        # Text Limits Section
        limits_frame = ttk.LabelFrame(scrollable_frame, text="Text Limits", padding="5")
        limits_frame.pack(fill="x", pady=(0, 10))
        
        limits = [
            ("Title Max Chars:", "title_max_chars_var", self.current_settings.title_max_chars),
            ("Item Max Chars:", "item_max_chars_var", self.current_settings.item_max_chars),
            ("Case Max Chars:", "case_max_chars_var", self.current_settings.case_max_chars),
            ("Max Title Lines:", "max_title_lines_var", self.current_settings.max_title_lines),
        ]
        
        for i, (label, var_name, value) in enumerate(limits):
            ttk.Label(limits_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 5))
            var = tk.IntVar(value=value)
            setattr(self, var_name, var)
            spin = ttk.Spinbox(limits_frame, from_=1, to=100, width=10,
                              textvariable=var, command=self._on_setting_changed)
            spin.grid(row=i, column=1, sticky="w", padx=(0, 10))
        
        # Visual Elements Section
        visual_frame = ttk.LabelFrame(scrollable_frame, text="Visual Elements", padding="5")
        visual_frame.pack(fill="x", pady=(0, 10))
        
        # Show Separator
        self.show_separator_var = tk.BooleanVar(value=self.current_settings.show_separator)
        ttk.Checkbutton(visual_frame, text="Show Separator Line", 
                       variable=self.show_separator_var,
                       command=self._on_setting_changed).grid(row=0, column=0, columnspan=2, sticky="w")
        
        # Separator Width
        ttk.Label(visual_frame, text="Separator Width:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.separator_width_var = tk.IntVar(value=self.current_settings.separator_width)
        ttk.Spinbox(visual_frame, from_=50, to=500, width=10,
                   textvariable=self.separator_width_var,
                   command=self._on_setting_changed).grid(row=1, column=1, sticky="w", padx=(0, 10))
        
        # Barcode Settings Section
        barcode_frame = ttk.LabelFrame(scrollable_frame, text="Barcode Settings", padding="5")
        barcode_frame.pack(fill="x", pady=(0, 10))
        
        barcode_settings = [
            ("Barcode Height:", "barcode_height_var", self.current_settings.barcode_height),
            ("Narrow Width:", "barcode_narrow_var", self.current_settings.barcode_narrow),
            ("Wide Width:", "barcode_wide_var", self.current_settings.barcode_wide),
        ]
        
        for i, (label, var_name, value) in enumerate(barcode_settings):
            ttk.Label(barcode_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 5))
            var = tk.IntVar(value=value)
            setattr(self, var_name, var)
            spin = ttk.Spinbox(barcode_frame, from_=1, to=100, width=10,
                              textvariable=var, command=self._on_setting_changed)
            spin.grid(row=i, column=1, sticky="w", padx=(0, 10))
        
        # HRI Position
        ttk.Label(barcode_frame, text="HRI Position:").grid(row=3, column=0, sticky="w", padx=(0, 5))
        self.barcode_hri_var = tk.StringVar(value=self.current_settings.barcode_hri)
        hri_combo = ttk.Combobox(barcode_frame, textvariable=self.barcode_hri_var,
                                values=["N", "A", "B", "O"], width=7,
                                state="readonly")
        hri_combo.grid(row=3, column=1, sticky="w", padx=(0, 10))
        hri_combo.bind("<<ComboboxSelected>>", lambda e: self._on_setting_changed())
        
        # Orientation Section
        orient_frame = ttk.LabelFrame(scrollable_frame, text="Label Orientation", padding="5")
        orient_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(orient_frame, text="Orientation:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.orientation_var = tk.StringVar(value=self.current_settings.orientation)
        orient_combo = ttk.Combobox(orient_frame, textvariable=self.orientation_var,
                                   values=["normal", "rotated90", "rotated180", "rotated270"],
                                   width=15, state="readonly")
        orient_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        orient_combo.bind("<<ComboboxSelected>>", lambda e: self._on_setting_changed())
        
        # Preview Settings Section
        preview_settings_frame = ttk.LabelFrame(scrollable_frame, text="Preview Settings", padding="5")
        preview_settings_frame.pack(fill="x", pady=(0, 10))
        
        preview_settings = [
            ("Title Font Size:", "preview_title_font_size_var", self.current_settings.preview_title_font_size),
            ("Text Font Size:", "preview_text_font_size_var", self.current_settings.preview_text_font_size),
        ]
        
        for i, (label, var_name, value) in enumerate(preview_settings):
            ttk.Label(preview_settings_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 5))
            var = tk.IntVar(value=value)
            setattr(self, var_name, var)
            spin = ttk.Spinbox(preview_settings_frame, from_=8, to=72, width=10,
                              textvariable=var, command=self._on_setting_changed)
            spin.grid(row=i, column=1, sticky="w", padx=(0, 10))
    
    def _create_preview_widget(self, parent):
        """Create the preview widget."""
        # Preview canvas
        self.preview_canvas = tk.Canvas(parent, bg="white", width=300, height=400)
        self.preview_canvas.pack(fill="both", expand=True)
        
        # Sample data for preview
        self.preview_data = {
            "title": "Sample Product Title",
            "item_number": "ITEM123456",
            "casepack": "12",
            "upc12": "123456789012"
        }
    
    def _on_setting_changed(self):
        """Called when any setting is changed - updates preview."""
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview with current settings."""
        try:
            # Get current settings from widgets
            settings = self._get_current_settings_from_widgets()
            
            # Get label dimensions
            dims = get_label_size_dots(self.label_size)
            
            # Render preview
            img = render_label_preview(
                width_dots=dims["width_dots"],
                height_dots=dims["height_dots"],
                title=self.preview_data["title"],
                item_number=self.preview_data["item_number"],
                casepack=self.preview_data["casepack"],
                upc12=self.preview_data["upc12"]
            )
            
            # Convert to Tkinter image
            tk_img = image_to_tk(img)
            
            # Update canvas
            self.preview_canvas.delete("all")
            
            # Scale image to fit canvas
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate scale to fit
                scale_x = canvas_width / img.width
                scale_y = canvas_height / img.height
                scale = min(scale_x, scale_y, 1.0)  # Don't scale up
                
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                
                # Resize image
                img_resized = img.resize((new_width, new_height))
                tk_img = image_to_tk(img_resized)
                
                # Center image
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                
                self.preview_canvas.create_image(x, y, anchor="nw", image=tk_img)
                self.preview_canvas.image = tk_img  # Keep reference
        
        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(150, 200, text="Preview Error", fill="red")
    
    def _get_current_settings_from_widgets(self) -> LabelSettings:
        """Get current settings from all widgets."""
        return LabelSettings(
            title_font=self.title_font_var.get(),
            text_font=self.text_font_var.get(),
            title_xy_mul_x=1,  # Fixed
            title_xy_mul_y=self.title_xy_mul_y_var.get(),
            x_margin=self.x_margin_var.get(),
            title_y=self.title_y_var.get(),
            item_y=self.item_y_var.get(),
            case_y=self.case_y_var.get(),
            barcode_y=self.barcode_y_var.get(),
            line_spacing=self.line_spacing_var.get(),
            title_max_chars=self.title_max_chars_var.get(),
            item_max_chars=self.item_max_chars_var.get(),
            case_max_chars=self.case_max_chars_var.get(),
            max_title_lines=self.max_title_lines_var.get(),
            show_separator=self.show_separator_var.get(),
            separator_width=self.separator_width_var.get(),
            separator_thickness=2,  # Fixed
            barcode_height=self.barcode_height_var.get(),
            barcode_narrow=self.barcode_narrow_var.get(),
            barcode_wide=self.barcode_wide_var.get(),
            barcode_hri=self.barcode_hri_var.get(),
            orientation=self.orientation_var.get(),
            preview_title_font_size=self.preview_title_font_size_var.get(),
            preview_text_font_size=self.preview_text_font_size_var.get()
        )
    
    def _reset_to_default(self):
        """Reset settings to default."""
        if messagebox.askyesno("Reset Settings", 
                              "Are you sure you want to reset all settings to default?"):
            self.current_settings = self.settings_manager.reset_to_default(
                self.printer_name, self.label_size)
            self._load_settings_to_widgets()
            self._update_preview()
    
    def _load_settings_to_widgets(self):
        """Load current settings into widgets."""
        # Update all widget variables
        self.title_font_var.set(self.current_settings.title_font)
        self.text_font_var.set(self.current_settings.text_font)
        self.title_xy_mul_y_var.set(self.current_settings.title_xy_mul_y)
        self.x_margin_var.set(self.current_settings.x_margin)
        self.title_y_var.set(self.current_settings.title_y)
        self.item_y_var.set(self.current_settings.item_y)
        self.case_y_var.set(self.current_settings.case_y)
        self.barcode_y_var.set(self.current_settings.barcode_y)
        self.line_spacing_var.set(self.current_settings.line_spacing)
        self.title_max_chars_var.set(self.current_settings.title_max_chars)
        self.item_max_chars_var.set(self.current_settings.item_max_chars)
        self.case_max_chars_var.set(self.current_settings.case_max_chars)
        self.max_title_lines_var.set(self.current_settings.max_title_lines)
        self.show_separator_var.set(self.current_settings.show_separator)
        self.separator_width_var.set(self.current_settings.separator_width)
        self.barcode_height_var.set(self.current_settings.barcode_height)
        self.barcode_narrow_var.set(self.current_settings.barcode_narrow)
        self.barcode_wide_var.set(self.current_settings.barcode_wide)
        self.barcode_hri_var.set(self.current_settings.barcode_hri)
        self.orientation_var.set(self.current_settings.orientation)
        self.preview_title_font_size_var.set(self.current_settings.preview_title_font_size)
        self.preview_text_font_size_var.set(self.current_settings.preview_text_font_size)
    
    def _apply(self):
        """Apply current settings."""
        try:
            settings = self._get_current_settings_from_widgets()
            self.settings_manager.save_settings(self.printer_name, self.label_size, settings)
            self.current_settings = settings
            
            if self.on_settings_changed:
                self.on_settings_changed()
            
            messagebox.showinfo("Settings Applied", "Settings have been saved and applied.")
        
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _ok(self):
        """Apply settings and close dialog."""
        self._apply()
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel changes and close dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show the settings dialog."""
        self.dialog.wait_window()
        return self.current_settings
