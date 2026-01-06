"""
Google Sheets API client for spreadsheet operations.

Supports service account and OAuth authentication methods.
"""

from pathlib import Path
from typing import Any, Literal

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsClient:
    """Google Sheets API client for spreadsheet operations."""

    def __init__(self, service):
        self._service = service

    @classmethod
    def from_service_account(cls, credentials_path: str | Path) -> "GoogleSheetsClient":
        """
        Authenticate using a service account JSON key file.

        Parameters
        ----------
        credentials_path
            Path to service account JSON file.

        Returns
        -------
        GoogleSheetsClient
            Authenticated client instance.
        """
        creds = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=SCOPES,
        )
        service = build("sheets", "v4", credentials=creds)
        return cls(service)

    @classmethod
    def from_oauth(
        cls,
        credentials_path: str | Path,
        token_path: str | Path = "sheets_token.json",
    ) -> "GoogleSheetsClient":
        """
        Authenticate using OAuth (interactive browser flow).

        Parameters
        ----------
        credentials_path
            Path to OAuth client secrets JSON file.
        token_path
            Path to store/load cached token.

        Returns
        -------
        GoogleSheetsClient
            Authenticated client instance.
        """
        creds = None
        token_path = Path(token_path)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            token_path.write_text(creds.to_json())

        service = build("sheets", "v4", credentials=creds)
        return cls(service)

    def create_spreadsheet(
        self,
        title: str,
        sheet_names: list[str] | None = None,
    ) -> dict:
        """
        Create a new spreadsheet.

        Parameters
        ----------
        title
            Title of the spreadsheet.
        sheet_names
            Optional list of sheet names to create (defaults to one sheet named "Sheet1").

        Returns
        -------
        dict
            Dict with spreadsheet_id, title, url, and sheets info.
        """
        sheets = []
        if sheet_names:
            sheets = [{"properties": {"title": name}} for name in sheet_names]
        else:
            sheets = [{"properties": {"title": "Sheet1"}}]

        spreadsheet_body = {
            "properties": {"title": title},
            "sheets": sheets,
        }

        spreadsheet = (
            self._service.spreadsheets()
            .create(body=spreadsheet_body, fields="spreadsheetId,properties,spreadsheetUrl,sheets")
            .execute()
        )

        return {
            "spreadsheet_id": spreadsheet.get("spreadsheetId"),
            "title": spreadsheet.get("properties", {}).get("title"),
            "url": spreadsheet.get("spreadsheetUrl"),
            "sheets": [
                {
                    "sheet_id": s["properties"]["sheetId"],
                    "title": s["properties"]["title"],
                }
                for s in spreadsheet.get("sheets", [])
            ],
        }

    def get_spreadsheet(self, spreadsheet_id: str) -> dict:
        """
        Get spreadsheet metadata.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.

        Returns
        -------
        dict
            Dict with spreadsheet_id, title, url, and sheets info.
        """
        spreadsheet = (
            self._service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="spreadsheetId,properties,spreadsheetUrl,sheets")
            .execute()
        )

        return {
            "spreadsheet_id": spreadsheet.get("spreadsheetId"),
            "title": spreadsheet.get("properties", {}).get("title"),
            "url": spreadsheet.get("spreadsheetUrl"),
            "sheets": [
                {
                    "sheet_id": s["properties"]["sheetId"],
                    "title": s["properties"]["title"],
                    "row_count": s["properties"]["gridProperties"]["rowCount"],
                    "column_count": s["properties"]["gridProperties"]["columnCount"],
                }
                for s in spreadsheet.get("sheets", [])
            ],
        }

    def read_values(
        self,
        spreadsheet_id: str,
        range: str,
        value_render_option: Literal["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"] = "FORMATTED_VALUE",
    ) -> list[list[Any]]:
        """
        Read values from a spreadsheet range.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        range
            The A1 notation range to read (e.g., "Sheet1!A1:D10" or "A1:D10").
        value_render_option
            How values should be rendered:
            - FORMATTED_VALUE: As displayed in the UI
            - UNFORMATTED_VALUE: Raw values without formatting
            - FORMULA: Formulas instead of computed values

        Returns
        -------
        list[list[Any]]
            2D list of cell values (rows x columns).
        """
        result = (
            self._service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueRenderOption=value_render_option,
            )
            .execute()
        )

        return result.get("values", [])

    def write_values(
        self,
        spreadsheet_id: str,
        range: str,
        values: list[list[Any]],
        value_input_option: Literal["RAW", "USER_ENTERED"] = "USER_ENTERED",
    ) -> dict:
        """
        Write values to a spreadsheet range.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        range
            The A1 notation range to write (e.g., "Sheet1!A1" or "A1").
        values
            2D list of values to write (rows x columns).
        value_input_option
            How input should be interpreted:
            - RAW: Values are stored as-is
            - USER_ENTERED: Values are parsed as if typed into the UI (formulas executed)

        Returns
        -------
        dict
            Dict with updated_range, updated_rows, updated_columns, and updated_cells.
        """
        body = {"values": values}

        result = (
            self._service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )

        return {
            "updated_range": result.get("updatedRange"),
            "updated_rows": result.get("updatedRows"),
            "updated_columns": result.get("updatedColumns"),
            "updated_cells": result.get("updatedCells"),
        }

    def append_values(
        self,
        spreadsheet_id: str,
        range: str,
        values: list[list[Any]],
        value_input_option: Literal["RAW", "USER_ENTERED"] = "USER_ENTERED",
        insert_data_option: Literal["OVERWRITE", "INSERT_ROWS"] = "INSERT_ROWS",
    ) -> dict:
        """
        Append values to a spreadsheet (adds rows after existing data).

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        range
            The A1 notation range to search for existing data (e.g., "Sheet1!A:D").
        values
            2D list of values to append (rows x columns).
        value_input_option
            How input should be interpreted (RAW or USER_ENTERED).
        insert_data_option
            How the data should be inserted:
            - OVERWRITE: Overwrite existing data
            - INSERT_ROWS: Insert new rows for the data

        Returns
        -------
        dict
            Dict with updated_range, updated_rows, updated_columns, and updated_cells.
        """
        body = {"values": values}

        result = (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption=value_input_option,
                insertDataOption=insert_data_option,
                body=body,
            )
            .execute()
        )

        updates = result.get("updates", {})
        return {
            "updated_range": updates.get("updatedRange"),
            "updated_rows": updates.get("updatedRows"),
            "updated_columns": updates.get("updatedColumns"),
            "updated_cells": updates.get("updatedCells"),
        }

    def clear_values(self, spreadsheet_id: str, range: str) -> str:
        """
        Clear values from a spreadsheet range.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        range
            The A1 notation range to clear (e.g., "Sheet1!A1:D10").

        Returns
        -------
        str
            The cleared range.
        """
        result = (
            self._service.spreadsheets()
            .values()
            .clear(spreadsheetId=spreadsheet_id, range=range, body={})
            .execute()
        )

        return result.get("clearedRange", range)

    def batch_update_values(
        self,
        spreadsheet_id: str,
        data: list[dict],
        value_input_option: Literal["RAW", "USER_ENTERED"] = "USER_ENTERED",
    ) -> dict:
        """
        Update multiple ranges in a single request.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        data
            List of dicts with "range" and "values" keys.
            Example: [{"range": "Sheet1!A1", "values": [[1, 2], [3, 4]]}]
        value_input_option
            How input should be interpreted (RAW or USER_ENTERED).

        Returns
        -------
        dict
            Dict with total_updated_rows, total_updated_columns, total_updated_cells,
            and total_updated_sheets.
        """
        body = {
            "valueInputOption": value_input_option,
            "data": data,
        }

        result = (
            self._service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
            .execute()
        )

        return {
            "total_updated_rows": result.get("totalUpdatedRows"),
            "total_updated_columns": result.get("totalUpdatedColumns"),
            "total_updated_cells": result.get("totalUpdatedCells"),
            "total_updated_sheets": result.get("totalUpdatedSheets"),
        }

    def add_sheet(
        self,
        spreadsheet_id: str,
        title: str,
        rows: int = 1000,
        columns: int = 26,
    ) -> dict:
        """
        Add a new sheet to an existing spreadsheet.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        title
            Title for the new sheet.
        rows
            Number of rows (default 1000).
        columns
            Number of columns (default 26).

        Returns
        -------
        dict
            Dict with sheet_id and title.
        """
        request = {
            "addSheet": {
                "properties": {
                    "title": title,
                    "gridProperties": {
                        "rowCount": rows,
                        "columnCount": columns,
                    },
                }
            }
        }

        result = (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [request]})
            .execute()
        )

        reply = result.get("replies", [{}])[0].get("addSheet", {})
        props = reply.get("properties", {})

        return {
            "sheet_id": props.get("sheetId"),
            "title": props.get("title"),
        }

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> bool:
        """
        Delete a sheet from a spreadsheet.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        sheet_id
            The ID of the sheet to delete (not the title).

        Returns
        -------
        bool
            True if deletion was successful.
        """
        request = {"deleteSheet": {"sheetId": sheet_id}}

        self._service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": [request]}
        ).execute()

        return True

    def rename_sheet(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        new_title: str,
    ) -> bool:
        """
        Rename a sheet.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        sheet_id
            The ID of the sheet to rename.
        new_title
            The new title for the sheet.

        Returns
        -------
        bool
            True if rename was successful.
        """
        request = {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "title": new_title,
                },
                "fields": "title",
            }
        }

        self._service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": [request]}
        ).execute()

        return True

    def get_sheet_id_by_title(self, spreadsheet_id: str, title: str) -> int | None:
        """
        Get a sheet's ID by its title.

        Parameters
        ----------
        spreadsheet_id
            The ID of the spreadsheet.
        title
            The title of the sheet.

        Returns
        -------
        int | None
            The sheet ID, or None if not found.
        """
        info = self.get_spreadsheet(spreadsheet_id)
        for sheet in info["sheets"]:
            if sheet["title"] == title:
                return sheet["sheet_id"]
        return None


def write_data(
    spreadsheet_id: str,
    range: str,
    values: list[list[Any]],
    credentials_path: str | Path,
) -> dict:
    """
    Convenience function to write data using service account.

    Parameters
    ----------
    spreadsheet_id
        The ID of the spreadsheet.
    range
        The A1 notation range to write.
    values
        2D list of values to write.
    credentials_path
        Path to service account JSON.

    Returns
    -------
    dict
        Dict with update info.
    """
    client = GoogleSheetsClient.from_service_account(credentials_path)
    return client.write_values(spreadsheet_id, range, values)


def read_data(
    spreadsheet_id: str,
    range: str,
    credentials_path: str | Path,
) -> list[list[Any]]:
    """
    Convenience function to read data using service account.

    Parameters
    ----------
    spreadsheet_id
        The ID of the spreadsheet.
    range
        The A1 notation range to read.
    credentials_path
        Path to service account JSON.

    Returns
    -------
    list[list[Any]]
        2D list of cell values.
    """
    client = GoogleSheetsClient.from_service_account(credentials_path)
    return client.read_values(spreadsheet_id, range)
