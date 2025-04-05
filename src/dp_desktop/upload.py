import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import requests


def upload_files(
        folder_path: Path,
        api_key: str,
        dataset_name: str,
        schema_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        error_callback: Optional[Callable[[Path, str], None]] = None,
        max_workers: int = 20
):
    """
    Upload and standardize all files in parallel.
    Calls progress_callback(files_completed, total_files) after each file finishes.
    Calls error_callback(file_path, error_message) on each failure (if provided),
    and continues processing the rest of the files.
    """

    files = list(folder_path.rglob('*.*'))
    allowed_set = {'.pdf', '.jpg', '.jpeg', '.png', '.txt', '.tiff', '.webp'}
    files = [f for f in files if f.suffix.lower() in allowed_set]

    total_files = len(files)
    if total_files == 0:
        return  # No files; nothing to do.

    if progress_callback:
        progress_callback(0, total_files)

    def _upload_and_standardize_file(file_path: Path):
        # 1) Encode and POST the file
        try:
            with open(file_path, 'rb') as f:
                file_contents = base64.b64encode(f.read()).decode()

            upload_url = "https://app.docupanda.io/document"
            payload = {
                "dataset": dataset_name,
                "document": {
                    "file": {
                        "contents": file_contents,
                        "filename": file_path.name
                    }
                }
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "X-API-Key": api_key
            }
            response = requests.post(upload_url, json=payload, headers=headers)
            response.raise_for_status()
            document_id = response.json().get('documentId')
            if not document_id:
                raise RuntimeError(f"No 'documentId' returned for {file_path.name}")

        except Exception as e:
            raise RuntimeError(f"Upload failed for {file_path.name}: {str(e)}") from e

        # 2) Poll until doc status is "completed"
        try:
            doc_get_url = f"https://app.docupanda.io/document/{document_id}"
            while True:
                time.sleep(2)
                get_resp = requests.get(doc_get_url, headers=headers)
                get_resp.raise_for_status()
                status = get_resp.json().get('status')
                if status == 'completed':
                    break
                elif status == 'failed':
                    raise RuntimeError(f"Processing failed for docId={document_id}")

        except Exception as e:
            raise RuntimeError(f"Polling document status failed for {file_path.name}: {str(e)}") from e

        # 3) Standardize if schema_id is provided
        if schema_id:
            try:
                std_url = "https://app.docupanda.io/standardize/batch"
                std_payload = {
                    "documentIds": [document_id],
                    "schemaId": schema_id
                }
                std_resp = requests.post(std_url, json=std_payload, headers=headers)
                std_resp.raise_for_status()
                standardization_ids = std_resp.json().get('standardizationIds')
                standardization_id = standardization_ids[0] if standardization_ids else None
                if not standardization_id:
                    raise RuntimeError(f"No 'standardizationId' returned for {file_path.name}")

                # 4) Poll for standardization to be "completed"
                std_get_url = f"https://app.docupanda.io/standardization/{standardization_id}"
                max_poll_attempts = 50
                for i in range(max_poll_attempts):
                    std_get_resp = requests.get(std_get_url, headers=headers)
                    # std_get_resp.raise_for_status()
                    # if this gets a 404 error, sleep and try again
                    if std_get_resp.status_code == 404:
                        time.sleep(10)
                        continue
                    # if we get here, it's a status other than 404 and we don't need to keep polling
                    break

            except Exception as e:
                raise RuntimeError(f"Standardization failed for {file_path.name}: {str(e)}") from e

        return True

    files_completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(_upload_and_standardize_file, file_path): file_path
            for file_path in files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()  # raises if file failed
                files_completed += 1
                if progress_callback:
                    progress_callback(files_completed, total_files)
            except Exception as e:
                if error_callback:
                    error_callback(file_path, str(e))
                else:
                    print(f"Error processing file {file_path}: {e}")
