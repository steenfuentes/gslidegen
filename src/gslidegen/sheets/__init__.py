"""
Google Sheets integration module.

Provides a client for creating, reading, updating, and deleting spreadsheet data.
"""

from gslidegen.sheets.client import GoogleSheetsClient, read_data, write_data

__all__ = [
    "GoogleSheetsClient",
    "read_data",
    "write_data",
]
