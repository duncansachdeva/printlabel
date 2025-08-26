"""Windows raw printing utilities.

This module provides functions to send raw bytes to a Windows printer
using the Windows spooler APIs via pywin32.
"""
from typing import Optional
import win32print


def list_installed_printers() -> list[str]:
	"""Return a list of installed printer names."""
	flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
	printers = win32print.EnumPrinters(flags)
	return [p[2] for p in printers]


def get_default_printer() -> Optional[str]:
	"""Return the default printer name, if available."""
	try:
		return win32print.GetDefaultPrinter()
	except win32print.error:
		return None


def send_raw(printer_name: str, data: bytes, job_name: str = "PrintLabel Job") -> None:
	"""Send raw ZPL/EPL bytes to the given printer.

	Raises win32print.error on failure.
	"""
	hPrinter = win32print.OpenPrinter(printer_name)
	try:
		hJob = win32print.StartDocPrinter(hPrinter, 1, (job_name, None, "RAW"))
		try:
			win32print.StartPagePrinter(hPrinter)
			win32print.WritePrinter(hPrinter, data)
			win32print.EndPagePrinter(hPrinter)
		finally:
			win32print.EndDocPrinter(hPrinter)
	finally:
		win32print.ClosePrinter(hPrinter)
