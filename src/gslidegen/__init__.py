"""
gslidegen - Tableau workbook export and PDF processing utilities.

This package provides tools for exporting Tableau workbooks to PDF and PowerPoint,
as well as utilities for PDF manipulation and image conversion.

Modules
-------
tableau
    Tableau REST API client for authentication and workbook exports.
pdf
    PDF utilities for page extraction and image conversion.
drive
    Google Drive client for file uploads and sharing.
sheets
    Google Sheets client for spreadsheet operations.
"""

from gslidegen.pdf.utils import extract_page, get_page_count, page_to_image
from gslidegen.tableau.client import TableauClient
from gslidegen.tableau.config import TableauConfig
from gslidegen.tableau.enums import Orientation, PageType
from gslidegen.drive.client import GoogleDriveClient, upload_image, upload_image_oauth
from gslidegen.sheets.client import GoogleSheetsClient, read_data, write_data

__all__ = [
    "TableauClient",
    "TableauConfig",
    "PageType",
    "Orientation",
    "extract_page",
    "get_page_count",
    "page_to_image",
    "GoogleDriveClient",
    "upload_image",
    "upload_image_oauth",
    "GoogleSheetsClient",
    "read_data",
    "write_data",
]
