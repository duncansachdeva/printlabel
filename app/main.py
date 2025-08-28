"""Main entry for the PrintLabel Windows app (Tkinter UI)."""
import logging
import os
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils.winprint import list_installed_printers, get_default_printer, send_raw
from app.printer_detection import guess_printer_language
from app.labels.zpl import build_zpl_label
from app.labels.epl import build_epl_label
from app.labels.sizes import LABEL_SIZES_DOTS
from app.utils.validation import ensure_upc12, sanitize_text
from app.utils.preview import render_label_preview, image_to_tk


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=os.path.join("logs", "app.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


class PrintLabelApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PrintLabel")
        self.geometry("560x700")
        self.resizable(False, False)

        setup_logging()
        logging.info("Application started")

        self.preview_image = None

        self._build_ui()
        self._load_printers()
        self._update_preview()

    def _build_ui(self) -> None:
        padding = {"padx": 10, "pady": 6}

        # Printer selection
        frm_printer = ttk.LabelFrame(self, text="Printer")
        frm_printer.pack(fill="x", **padding)

        ttk.Label(frm_printer, text="Installed:").grid(row=0, column=0, sticky="w")
        self.cbo_printers = ttk.Combobox(frm_printer, state="readonly", width=50)
        self.cbo_printers.grid(row=0, column=1, columnspan=3, sticky="we", padx=6)
        self.cbo_printers.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        ttk.Label(frm_printer, text="Language:").grid(row=1, column=0, sticky="w")
        self.cbo_language = ttk.Combobox(frm_printer, state="readonly", values=["Auto", "ZPL", "EPL"], width=12)
        self.cbo_language.set("Auto")
        self.cbo_language.grid(row=1, column=1, sticky="w", padx=6)
        self.cbo_language.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        ttk.Label(frm_printer, text="Size:").grid(row=1, column=2, sticky="e")
        self.cbo_size = ttk.Combobox(frm_printer, state="readonly", values=list(LABEL_SIZES_DOTS.keys()), width=12)
        self.cbo_size.set("4x6")
        self.cbo_size.grid(row=1, column=3, sticky="w")
        self.cbo_size.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        # Fields
        frm_fields = ttk.LabelFrame(self, text="Label Data")
        frm_fields.pack(fill="x", **padding)

        ttk.Label(frm_fields, text="Item Number:").grid(row=0, column=0, sticky="e")
        self.txt_item = ttk.Entry(frm_fields, width=50)
        self.txt_item.grid(row=0, column=1, sticky="we", padx=6)
        self.txt_item.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frm_fields, text="UPC (11 or 12 digits):").grid(row=1, column=0, sticky="e")
        self.txt_upc = ttk.Entry(frm_fields, width=50)
        self.txt_upc.grid(row=1, column=1, sticky="we", padx=6)
        self.txt_upc.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frm_fields, text="Title:").grid(row=2, column=0, sticky="e")
        self.txt_title = ttk.Entry(frm_fields, width=50)
        self.txt_title.grid(row=2, column=1, sticky="we", padx=6)
        self.txt_title.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frm_fields, text="Casepack:").grid(row=3, column=0, sticky="e")
        self.txt_case = ttk.Entry(frm_fields, width=50)
        self.txt_case.grid(row=3, column=1, sticky="we", padx=6)
        self.txt_case.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frm_fields, text="Copies:").grid(row=4, column=0, sticky="e")
        self.spn_copies = tk.Spinbox(frm_fields, from_=1, to=999, width=6)
        self.spn_copies.delete(0, "end")
        self.spn_copies.insert(0, "1")
        self.spn_copies.grid(row=4, column=1, sticky="w", padx=6)

        # Preview area
        frm_preview = ttk.LabelFrame(self, text="Preview")
        frm_preview.pack(fill="both", expand=True, **padding)
        self.cnv_preview = tk.Canvas(frm_preview, width=520, height=260, bg="white")
        self.cnv_preview.pack(fill="both", expand=True)

        # Actions
        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill="x", **padding)

        self.btn_print = ttk.Button(frm_actions, text="Print", command=self._on_print)
        self.btn_print.pack(side="right")

    def _load_printers(self) -> None:
        try:
            printers = list_installed_printers()
        except Exception as ex:
            logging.exception("Failed to enumerate printers")
            messagebox.showerror("Error", f"Failed to enumerate printers: {ex}")
            printers = []

        self.cbo_printers["values"] = printers
        default = get_default_printer()
        if default and default in printers:
            self.cbo_printers.set(default)
        elif printers:
            self.cbo_printers.set(printers[0])

    def _resolve_language(self, printer_name: str) -> str:
        selected = self.cbo_language.get()
        if selected == "Auto":
            return guess_printer_language(printer_name)
        return selected

    def _update_preview(self) -> None:
        try:
            size_key = self.cbo_size.get() or "4x6"
            dims = LABEL_SIZES_DOTS.get(size_key) or LABEL_SIZES_DOTS["4x6"]

            title = self.txt_title.get().strip()
            item_number = self.txt_item.get().strip()
            casepack = self.txt_case.get().strip()
            upc12 = ensure_upc12(self.txt_upc.get().strip() or "") or ""

            img = render_label_preview(
                width_dots=dims["width_dots"],
                height_dots=dims["height_dots"],
                title=title,
                item_number=item_number,
                casepack=casepack,
                upc12=upc12,
            )

            # Scale to fit canvas while preserving aspect
            cnv_w = int(self.cnv_preview["width"]) if str(self.cnv_preview["width"]).isdigit() else 520
            cnv_h = int(self.cnv_preview["height"]) if str(self.cnv_preview["height"]).isdigit() else 260
            scale = min(cnv_w / img.width, cnv_h / img.height)
            if scale <= 0:
                scale = 1.0
            disp = img.resize((int(img.width * scale), int(img.height * scale)))
            self.preview_image = image_to_tk(disp)
            self.cnv_preview.delete("all")
            self.cnv_preview.create_image(cnv_w // 2, cnv_h // 2, image=self.preview_image)
        except Exception:
            logging.warning("Failed to update preview", exc_info=True)

    def _on_print(self) -> None:
        printer_name = self.cbo_printers.get()
        if not printer_name:
            messagebox.showwarning("Printer", "Please select a printer.")
            return

        size_key = self.cbo_size.get() or "4x6"

        item_number = sanitize_text(self.txt_item.get().strip(), 64)
        title = sanitize_text(self.txt_title.get().strip(), 64)
        casepack = sanitize_text(self.txt_case.get().strip(), 32)

        upc_raw = self.txt_upc.get().strip()
        upc12 = ensure_upc12(upc_raw) if upc_raw else ""
        if upc_raw and not upc12:
            messagebox.showwarning("UPC", "UPC must be 11 or 12 digits with a valid check digit.")
            return

        try:
            copies = int(self.spn_copies.get())
        except Exception:
            copies = 1
        if copies < 1:
            copies = 1

        lang = self._resolve_language(printer_name)

        try:
            if lang == "EPL":
                payload = build_epl_label(
                    size_key=size_key,
                    item_number=item_number,
                    upc12=upc12,
                    title=title,
                    casepack=casepack,
                    copies=copies,
                )
            else:
                payload = build_zpl_label(
                    size_key=size_key,
                    item_number=item_number,
                    upc12=upc12,
                    title=title,
                    casepack=casepack,
                    copies=copies,
                )

            # Write debug payload to logs for troubleshooting
            try:
                fn = os.path.join("logs", f"payload_{lang.lower()}.txt")
                with open(fn, "wb") as f:
                    f.write(payload)
            except Exception:
                logging.warning("Failed to write payload debug file", exc_info=True)

            logging.info("Sending %s job to %s (%d bytes)", lang, printer_name, len(payload))
            send_raw(printer_name, payload, job_name=f"PrintLabel ({lang})")
            messagebox.showinfo("Printed", f"Sent {copies} label(s) to {printer_name} ({lang}).")
        except Exception as ex:
            logging.exception("Failed to print")
            messagebox.showerror("Error", f"Failed to print: {ex}")


if __name__ == "__main__":
    app = PrintLabelApp()
    app.mainloop()
