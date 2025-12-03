# gslidegen

Export Tableau workbooks to Google Drive as images.

## What it does

1. Downloads workbook from Tableau as PDF
2. Converts each page to PNG
3. Uploads to Google Drive (Shared Drive)

## Setup

```bash
uv sync
cp .env.example .env
```

### Requirements

- Tableau Server/Cloud with Personal Access Token
- Google Cloud service account with Drive API enabled
- Service account added to a Shared Drive as Content Manager

## Usage

```bash
uv run python main.py
```

## Configuration

Set in `.env`:

| Variable | Description |
|----------|-------------|
| `TABLEAU_SERVER` | Tableau server URL |
| `TABLEAU_SITE_CONTENT_URL` | Site content URL |
| `TABLEAU_TOKEN_NAME` | PAT name |
| `TABLEAU_TOKEN_SECRET` | PAT secret |
| `GOOGLE_SERVICE_ACCOUNT_PATH` | Path to service account JSON |
| `GOOGLE_DRIVE_FOLDER_ID` | Target folder ID in Shared Drive |

## Programmatic Usage

```python
from gslidegen import (
    GoogleDriveClient,
    TableauClient,
    TableauConfig,
    get_page_count,
    page_to_image,
)

config = TableauConfig(server=..., site_content_url=..., token_name=..., token_secret=...)
with TableauClient(config) as client:
    client.download_workbook_pdf(workbook_id, "output.pdf")

page_to_image("output.pdf", "page1.png", page_number=1, dpi=300)

drive = GoogleDriveClient.from_service_account("service-account.json")
drive.upload_file("page1.png", folder_id="...")
```
