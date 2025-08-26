## PrintLabel (Windows, Python)

A simple Windows desktop app to print labels on Zebra printers (e.g., LP2844, ZM400) using ZPL or EPL.

### Quick start

1. Create and activate a virtual environment
   - PowerShell
     ```powershell
     python -m venv .venv
     .venv\\Scripts\\Activate.ps1
     ```
2. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the app
   ```powershell
   python -m app.main
   ```

### Features
- Select installed Windows printers
- Auto-detect label language (ZPL/EPL) by printer name, with manual override
- Supports common sizes: 2x1 in, 4x6 in (203 dpi)
- Fields: Item Number, UPC, Title, Casepack, Copies

### Notes
- Ensure your Zebra printer is installed in Windows and configured for raw passthrough.
- ZPL and EPL are sent as raw bytes via the Windows print spooler.
- For LP2844 family, EPL is typically required. For ZM400, ZPL is typical.

### Packaging (optional)
If you plan to distribute, consider PyInstaller:
```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name PrintLabel app/main.py
```
