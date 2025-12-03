"""
Google Drive API client for file uploads.

Supports service account and OAuth authentication methods.
"""

from pathlib import Path
from typing import Literal

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class GoogleDriveClient:
    """Google Drive API client for file uploads."""

    def __init__(self, service):
        self._service = service

    @classmethod
    def from_service_account(cls, credentials_path: str | Path) -> "GoogleDriveClient":
        """
        Authenticate using a service account JSON key file.

        Parameters
        ----------
        credentials_path
            Path to service account JSON file.

        Returns
        -------
        GoogleDriveClient
            Authenticated client instance.
        """
        creds = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=SCOPES,
        )
        service = build("drive", "v3", credentials=creds)
        return cls(service)

    @classmethod
    def from_oauth(
        cls,
        credentials_path: str | Path,
        token_path: str | Path = "token.json",
    ) -> "GoogleDriveClient":
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
        GoogleDriveClient
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

        service = build("drive", "v3", credentials=creds)
        return cls(service)

    def upload_file(
        self,
        file_path: str | Path,
        name: str | None = None,
        folder_id: str | None = None,
        mime_type: str | None = None,
    ) -> dict:
        """
        Upload a file to Google Drive.

        Parameters
        ----------
        file_path
            Path to the file to upload.
        name
            Name for the file in Drive (defaults to local filename).
        folder_id
            Optional folder ID to upload into.
        mime_type
            Optional MIME type (auto-detected from extension if not provided).

        Returns
        -------
        dict
            Dict with file id, name, and web_view_link.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if name is None:
            name = file_path.name

        if mime_type is None:
            mime_type = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")

        file_metadata = {"name": name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=False)

        file = (
            self._service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id,name,webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )

        return {
            "id": file.get("id"),
            "name": file.get("name"),
            "web_view_link": file.get("webViewLink"),
        }

    def create_folder(
        self,
        name: str,
        parent_folder_id: str | None = None,
    ) -> dict:
        """
        Create a folder in Google Drive.

        Parameters
        ----------
        name
            Folder name.
        parent_folder_id
            Optional parent folder ID.

        Returns
        -------
        dict
            Dict with folder id and name.
        """
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        folder = (
            self._service.files()
            .create(body=file_metadata, fields="id,name")
            .execute()
        )

        return {
            "id": folder.get("id"),
            "name": folder.get("name"),
        }

    def list_files(
        self,
        folder_id: str | None = None,
        mime_type: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """
        List files in Drive or a specific folder.

        Parameters
        ----------
        folder_id
            Optional folder ID to list contents of.
        mime_type
            Optional filter by MIME type.
        page_size
            Number of results per page.

        Returns
        -------
        list[dict]
            List of dicts with file id, name, and mime_type.
        """
        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if mime_type:
            query_parts.append(f"mimeType='{mime_type}'")
        query_parts.append("trashed=false")

        query = " and ".join(query_parts)

        results = (
            self._service.files()
            .list(q=query, pageSize=page_size, fields="files(id,name,mimeType)")
            .execute()
        )

        return [
            {"id": f["id"], "name": f["name"], "mime_type": f["mimeType"]}
            for f in results.get("files", [])
        ]

    def share_file(
        self,
        file_id: str,
        role: Literal["reader", "writer", "commenter"] = "reader",
        type: Literal["anyone", "user", "group", "domain"] = "anyone",
        email: str | None = None,
    ) -> str:
        """
        Share a file and return the shareable link.

        Parameters
        ----------
        file_id
            ID of the file to share.
        role
            Permission level.
        type
            Who to share with.
        email
            Email address (required if type is 'user' or 'group').

        Returns
        -------
        str
            Web view link for the file.
        """
        permission = {"role": role, "type": type}
        if email and type in ("user", "group"):
            permission["emailAddress"] = email

        self._service.permissions().create(
            fileId=file_id,
            body=permission,
        ).execute()

        file = self._service.files().get(fileId=file_id, fields="webViewLink").execute()

        return file.get("webViewLink")


def upload_image(
    image_path: str | Path,
    credentials_path: str | Path,
    folder_id: str | None = None,
    share: bool = False,
) -> dict:
    """
    Convenience function to upload an image using service account.

    Parameters
    ----------
    image_path
        Path to image file.
    credentials_path
        Path to service account JSON.
    folder_id
        Optional destination folder ID.
    share
        If True, make file publicly viewable.

    Returns
    -------
    dict
        Dict with id, name, and web_view_link.
    """
    client = GoogleDriveClient.from_service_account(credentials_path)
    result = client.upload_file(image_path, folder_id=folder_id)

    if share:
        result["web_view_link"] = client.share_file(result["id"])

    return result


def upload_image_oauth(
    image_path: str | Path,
    credentials_path: str | Path,
    token_path: str | Path = "token.json",
    folder_id: str | None = None,
    share: bool = False,
) -> dict:
    """
    Convenience function to upload an image using OAuth.

    Parameters
    ----------
    image_path
        Path to image file.
    credentials_path
        Path to OAuth client secrets JSON.
    token_path
        Path to store/load cached token.
    folder_id
        Optional destination folder ID.
    share
        If True, make file publicly viewable.

    Returns
    -------
    dict
        Dict with id, name, and web_view_link.
    """
    client = GoogleDriveClient.from_oauth(credentials_path, token_path)
    result = client.upload_file(image_path, folder_id=folder_id)

    if share:
        result["web_view_link"] = client.share_file(result["id"])

    return result
