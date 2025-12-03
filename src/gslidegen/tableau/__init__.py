"""
Tableau REST API client module.

This module provides classes and functions for interacting with
Tableau Server and Tableau Cloud via the REST API.

Classes
-------
TableauClient
    Client for authenticating and interacting with the Tableau REST API.
TableauConfig
    Configuration dataclass for Tableau connection settings.
PageType
    Enumeration of supported PDF page sizes.
Orientation
    Enumeration of page orientations (portrait/landscape).
"""

from gslidegen.tableau.client import TableauClient
from gslidegen.tableau.config import TableauConfig
from gslidegen.tableau.enums import Orientation, PageType

__all__ = [
    "TableauClient",
    "TableauConfig",
    "PageType",
    "Orientation",
]
