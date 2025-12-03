"""
Tableau REST API client for interacting with Tableau Server/Cloud.

This module provides the TableauClient class for authenticating with Tableau,
listing workbooks, and downloading exports in various formats.
"""

from pathlib import Path
from typing import Self
import xml.etree.ElementTree as ET

import requests

from gslidegen.tableau.config import TableauConfig
from gslidegen.tableau.enums import Orientation, PageType


class TableauClient:
    """
    Client for interacting with the Tableau REST API.

    This client handles authentication via Personal Access Tokens (PAT)
    and provides methods for listing and exporting workbooks.

    Parameters
    ----------
    config : TableauConfig
        Configuration object containing server URL and credentials.

    Attributes
    ----------
    config : TableauConfig
        The configuration used for this client.
    token : str | None
        The authentication token after signing in.
    site_id : str | None
        The site ID after signing in.

    Examples
    --------
    >>> config = TableauConfig(
    ...     server="https://10ax.online.tableau.com/",
    ...     site_content_url="my-site",
    ...     token_name="my-token",
    ...     token_secret="secret",
    ... )
    >>> with TableauClient(config) as client:
    ...     workbooks = client.list_workbooks()
    """

    _NAMESPACE = {"t": "http://tableau.com/api"}

    def __init__(self, config: TableauConfig) -> None:
        self.config = config
        self.token: str | None = None
        self.site_id: str | None = None

    def __enter__(self) -> Self:
        """Sign in when entering context manager."""
        self.sign_in()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sign out when exiting context manager."""
        self.sign_out()

    def _build_url(self, endpoint: str) -> str:
        """
        Build full API URL for the given endpoint.

        Parameters
        ----------
        endpoint : str
            API endpoint path (e.g., "auth/signin").

        Returns
        -------
        str
            Full URL for the API endpoint.
        """
        return f"{self.config.server}/api/{self.config.api_version}/{endpoint}"

    def _get_headers(self) -> dict[str, str]:
        """
        Get HTTP headers for authenticated requests.

        Returns
        -------
        dict[str, str]
            Headers including auth token if available.
        """
        headers = {"Content-Type": "application/xml"}
        if self.token:
            headers["X-Tableau-Auth"] = self.token
        return headers

    def sign_in(self) -> tuple[str, str]:
        """
        Authenticate to Tableau using Personal Access Token.

        Returns
        -------
        tuple[str, str]
            Tuple of (auth_token, site_id).

        Raises
        ------
        ValueError
            If credentials are not found in the response.
        requests.HTTPError
            If the HTTP request fails.
        """
        url = self._build_url("auth/signin")

        payload = f"""
        <tsRequest>
            <credentials personalAccessTokenName="{self.config.token_name}"
                         personalAccessTokenSecret="{self.config.token_secret}">
                <site contentUrl="{self.config.site_content_url}" />
            </credentials>
        </tsRequest>
        """

        response = requests.post(
            url, data=payload, headers={"Content-Type": "application/xml"}
        )
        response.raise_for_status()

        root = ET.fromstring(response.text)
        creds = root.find(".//t:credentials", self._NAMESPACE)

        if creds is None:
            raise ValueError(f"No credentials in response: {response.text}")

        self.token = creds.get("token")
        site_elem = creds.find("t:site", self._NAMESPACE)
        self.site_id = site_elem.get("id") if site_elem is not None else None

        return self.token, self.site_id

    def sign_out(self) -> None:
        """
        Sign out and invalidate the current authentication token.

        This method is safe to call even if not signed in.
        """
        if self.token:
            url = self._build_url("auth/signout")
            requests.post(url, headers={"X-Tableau-Auth": self.token})
            self.token = None
            self.site_id = None

    def list_workbooks(self, page_size: int = 100) -> list[dict]:
        """
        List all workbooks on the authenticated site.

        Parameters
        ----------
        page_size : int, optional
            Number of workbooks per page. Default is 100.

        Returns
        -------
        list[dict]
            List of workbook dictionaries with keys:
            - id: Workbook ID
            - name: Workbook name
            - project_name: Name of the containing project
            - owner_name: Name of the workbook owner

        Raises
        ------
        RuntimeError
            If not authenticated.
        requests.HTTPError
            If the HTTP request fails.
        """
        if not self.token or not self.site_id:
            raise RuntimeError("Not authenticated. Call sign_in() first.")

        workbooks = []
        page_number = 1

        while True:
            url = self._build_url(f"sites/{self.site_id}/workbooks")
            params = {"pageSize": page_size, "pageNumber": page_number}

            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()

            root = ET.fromstring(response.text)
            pagination = root.find(".//t:pagination", self._NAMESPACE)
            total_available = int(pagination.get("totalAvailable", 0))

            for wb in root.findall(".//t:workbook", self._NAMESPACE):
                project = wb.find("t:project", self._NAMESPACE)
                owner = wb.find("t:owner", self._NAMESPACE)
                workbooks.append(
                    {
                        "id": wb.get("id"),
                        "name": wb.get("name"),
                        "project_name": (
                            project.get("name") if project is not None else None
                        ),
                        "owner_name": owner.get("name") if owner is not None else None,
                    }
                )

            if len(workbooks) >= total_available:
                break
            page_number += 1

        return workbooks

    def download_workbook_pdf(
        self,
        workbook_id: str,
        output_path: str | Path,
        page_type: PageType = PageType.LETTER,
        orientation: Orientation = Orientation.PORTRAIT,
        max_age: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> Path:
        """
        Download a workbook as a PDF file.

        Parameters
        ----------
        workbook_id : str
            The ID of the workbook to download.
        output_path : str | Path
            Path where the PDF will be saved.
        page_type : PageType, optional
            Page size for the PDF. Default is LETTER.
        orientation : Orientation, optional
            Page orientation. Default is PORTRAIT.
        max_age : int | None, optional
            Maximum age in minutes for cached data. If None, uses server default.
        filters : dict[str, str] | None, optional
            View filters to apply as field_name: value pairs.

        Returns
        -------
        Path
            Path to the saved PDF file.

        Raises
        ------
        RuntimeError
            If not authenticated.
        requests.HTTPError
            If the HTTP request fails.
        """
        if not self.token or not self.site_id:
            raise RuntimeError("Not authenticated. Call sign_in() first.")

        url = self._build_url(f"sites/{self.site_id}/workbooks/{workbook_id}/pdf")

        params = {
            "type": page_type.value,
            "orientation": orientation.value,
        }
        if max_age is not None:
            params["maxAge"] = max_age
        if filters:
            for field, value in filters.items():
                params[f"vf_{field}"] = value

        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()

        output_path = Path(output_path)
        output_path.write_bytes(response.content)

        return output_path

    def download_workbook_powerpoint(
        self,
        workbook_id: str,
        output_path: str | Path,
        max_age: int | None = None,
    ) -> Path:
        """
        Download a workbook as a PowerPoint file.

        Parameters
        ----------
        workbook_id : str
            The ID of the workbook to download.
        output_path : str | Path
            Path where the PowerPoint file will be saved.
        max_age : int | None, optional
            Maximum age in minutes for cached data. If None, uses server default.

        Returns
        -------
        Path
            Path to the saved PowerPoint file.

        Raises
        ------
        RuntimeError
            If not authenticated.
        requests.HTTPError
            If the HTTP request fails.
        """
        if not self.token or not self.site_id:
            raise RuntimeError("Not authenticated. Call sign_in() first.")

        url = self._build_url(
            f"sites/{self.site_id}/workbooks/{workbook_id}/powerpoint"
        )

        params = {}
        if max_age is not None:
            params["maxAge"] = max_age

        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()

        output_path = Path(output_path)
        output_path.write_bytes(response.content)

        return output_path
