"""
Configuration dataclass for Tableau Server/Cloud connections.

This module provides the TableauConfig dataclass used to store
authentication and connection details for the Tableau REST API.
"""

from dataclasses import dataclass


@dataclass
class TableauConfig:
    """
    Configuration for connecting to Tableau Server or Tableau Cloud.

    Parameters
    ----------
    server : str
        Base URL of the Tableau server (e.g., "https://10ax.online.tableau.com/").
    site_content_url : str
        The content URL (site ID) for the Tableau site.
    token_name : str
        Name of the Personal Access Token for authentication.
    token_secret : str
        Secret value of the Personal Access Token.
    api_version : str, optional
        Tableau REST API version to use. Default is "3.21".

    Examples
    --------
    >>> config = TableauConfig(
    ...     server="https://10ax.online.tableau.com/",
    ...     site_content_url="my-site",
    ...     token_name="my-token",
    ...     token_secret="secret-value",
    ... )
    """

    server: str
    site_content_url: str
    token_name: str
    token_secret: str
    api_version: str = "3.21"
