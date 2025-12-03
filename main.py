"""
Main entry point for gslidegen.

Run with: uv run python main.py
"""

import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from gslidegen import (
    GoogleDriveClient,
    Orientation,
    PageType,
    TableauClient,
    TableauConfig,
    get_page_count,
    page_to_image,
)


def main() -> int:
    """
    Run the Tableau to Google Drive pipeline.

    Downloads a workbook from Tableau as PDF, converts each page to PNG,
    and uploads all images to Google Drive.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure).
    """
    load_dotenv()

    tableau_config = TableauConfig(
        server=os.environ["TABLEAU_SERVER"],
        site_content_url=os.environ["TABLEAU_SITE_CONTENT_URL"],
        token_name=os.environ["TABLEAU_TOKEN_NAME"],
        token_secret=os.environ["TABLEAU_TOKEN_SECRET"],
    )

    drive_client = GoogleDriveClient.from_service_account(
        os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"]
    )
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

    work_dir = Path(tempfile.mkdtemp())

    try:
        with TableauClient(tableau_config) as tableau_client:
            workbooks = tableau_client.list_workbooks()

            if not workbooks:
                print("No workbooks found")
                return 1

            workbook = workbooks[0]
            print(f"Exporting workbook: {workbook['name']}")

            pdf_path = work_dir / f"{workbook['name']}.pdf"
            tableau_client.download_workbook_pdf(
                workbook_id=workbook["id"],
                output_path=pdf_path,
                page_type=PageType.LETTER,
                orientation=Orientation.LANDSCAPE,
                max_age=1,
            )
            print(f"Downloaded PDF: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")

            page_count = get_page_count(pdf_path)
            print(f"Converting {page_count} pages to images...")

            image_paths = []
            for page_num in range(1, page_count + 1):
                image_path = work_dir / f"{workbook['name']}_page{page_num}.png"
                page_to_image(
                    input_path=pdf_path,
                    output_path=image_path,
                    page_number=page_num,
                    dpi=300,
                )
                image_paths.append(image_path)
                print(f"  Page {page_num}/{page_count}: {image_path.name}")

            print(f"Uploading {len(image_paths)} images to Google Drive...")

            uploaded_files = []
            for image_path in image_paths:
                result = drive_client.upload_file(
                    file_path=image_path,
                    folder_id=folder_id,
                )
                uploaded_files.append(result)
                print(f"  Uploaded: {result['name']}")

            for image_path in image_paths:
                image_path.unlink()
            pdf_path.unlink()
            work_dir.rmdir()
            print("Cleaned up local files")

            print("\nUploaded files:")
            for result in uploaded_files:
                print(f"  {result['name']}: {result.get('web_view_link', 'N/A')}")

        return 0

    except requests.HTTPError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return 1
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        print("Copy .env.example to .env and fill in your credentials.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
