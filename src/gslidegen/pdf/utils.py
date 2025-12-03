"""
PDF utility functions for manipulation and conversion.

This module provides functions for extracting pages from PDFs,
getting page counts, and converting PDF pages to images.
"""

from pathlib import Path

from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter


def extract_page(
    input_path: str | Path,
    output_path: str | Path,
    page_number: int,
) -> Path:
    """
    Extract a single page from a PDF file.

    Parameters
    ----------
    input_path : str | Path
        Path to the source PDF file.
    output_path : str | Path
        Path where the extracted page will be saved.
    page_number : int
        Page number to extract (1-indexed).

    Returns
    -------
    Path
        Path to the output file.

    Raises
    ------
    ValueError
        If page_number is out of range.
    FileNotFoundError
        If input file does not exist.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    reader = PdfReader(input_path)
    writer = PdfWriter()

    page_index = page_number - 1

    if page_index < 0 or page_index >= len(reader.pages):
        raise ValueError(f"Page {page_number} out of range (1-{len(reader.pages)})")

    writer.add_page(reader.pages[page_index])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def get_page_count(input_path: str | Path) -> int:
    """
    Get the number of pages in a PDF file.

    Parameters
    ----------
    input_path : str | Path
        Path to the PDF file.

    Returns
    -------
    int
        Number of pages in the PDF.

    Raises
    ------
    FileNotFoundError
        If input file does not exist.
    """
    return len(PdfReader(input_path).pages)


def page_to_image(
    input_path: str | Path,
    output_path: str | Path,
    page_number: int,
    dpi: int = 200,
) -> Path:
    """
    Convert a single PDF page to a PNG image.

    Parameters
    ----------
    input_path : str | Path
        Path to the source PDF file.
    output_path : str | Path
        Path where the PNG image will be saved.
    page_number : int
        Page number to convert (1-indexed).
    dpi : int, optional
        Resolution in dots per inch. Default is 200.

    Returns
    -------
    Path
        Path to the output image file.

    Raises
    ------
    FileNotFoundError
        If input file does not exist.
    IndexError
        If page_number is out of range.

    Notes
    -----
    Requires poppler to be installed on the system for pdf2image to work.
    """
    images = convert_from_path(
        input_path,
        first_page=page_number,
        last_page=page_number,
        dpi=dpi,
    )

    output_path = Path(output_path)
    images[0].save(output_path, "PNG")

    return output_path
