"""
Enumerations for Tableau export configuration.

This module provides enums for PDF page types and orientations
used when exporting workbooks from Tableau.
"""

from enum import Enum


class PageType(Enum):
    """
    Page size types supported by Tableau PDF export.

    Attributes
    ----------
    A3 : str
        A3 paper size (297 x 420 mm).
    A4 : str
        A4 paper size (210 x 297 mm).
    A5 : str
        A5 paper size (148 x 210 mm).
    B5 : str
        B5 paper size (176 x 250 mm).
    EXECUTIVE : str
        Executive paper size (7.25 x 10.5 inches).
    FOLIO : str
        Folio paper size (8.5 x 13 inches).
    LEDGER : str
        Ledger paper size (11 x 17 inches).
    LEGAL : str
        Legal paper size (8.5 x 14 inches).
    LETTER : str
        Letter paper size (8.5 x 11 inches).
    NOTE : str
        Note paper size (7.5 x 10 inches).
    QUARTO : str
        Quarto paper size (8.5 x 10.83 inches).
    TABLOID : str
        Tabloid paper size (11 x 17 inches).
    """

    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    B5 = "B5"
    EXECUTIVE = "Executive"
    FOLIO = "Folio"
    LEDGER = "Ledger"
    LEGAL = "Legal"
    LETTER = "Letter"
    NOTE = "Note"
    QUARTO = "Quarto"
    TABLOID = "Tabloid"


class Orientation(Enum):
    """
    Page orientation for Tableau PDF export.

    Attributes
    ----------
    PORTRAIT : str
        Portrait orientation (height > width).
    LANDSCAPE : str
        Landscape orientation (width > height).
    """

    PORTRAIT = "Portrait"
    LANDSCAPE = "Landscape"
