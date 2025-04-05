import base64
import logging
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

    - Calls progress_callback(files_completed, total_files) after each file finishes.
    - Calls error_callback(file_path, error_message) on each failure (if provided),
      and continues processing the rest of the files.
    - Writes logs for each step (upload, poll, standardization) at INFO level.
      Any errors are logged at ERROR level.
    """

    # Log the start of upload
    logging.info(f"Scanning folder: {folder_path}")

    # Collect permissible files
    allowed_set = {'.pdf', '.jpg', '.jpeg', '.png', '.txt', '.tiff', '.webp'}
    all_files = list(folder_path.rglob('*.*'))
    files = [f for f in all_files if f.suffix.lower() in allowed_set]

    total_files = len(files)
    logging.info(f"Found {len(all_files)} total files, "
                 f"{total_files} are valid (allowed extensions: {allowed_set}).")

    if total_files == 0:
        logging.info("No valid files to process; returning early.")
        return

    # Let the user/UI know: starting at 0 of total_files
    if progress_callback:
        progress_callback(0, total_files)

    def _upload_and_standardize_file(file_path: Path):
        # 1) Encode and POST the file
        logging.info(f"Starting upload for: {file_path.name}")
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

            logging.info(f"Upload success for: {file_path.name}, docId={document_id}")

        except Exception as e:
            logging.error(f"Upload failed for {file_path.name}: {str(e)}", exc_info=True)
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
                    logging.info(f"Document {file_path.name} (docId={document_id}) has status 'completed'.")
                    break
                elif status == 'failed':
                    logging.error(f"Document {file_path.name} (docId={document_id}) has status 'failed'.")
                    raise RuntimeError(f"Processing failed for docId={document_id}")
                # Otherwise keep polling

        except Exception as e:
            logging.error(f"Polling document status failed for {file_path.name}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Polling document status failed for {file_path.name}: {str(e)}") from e

        # 3) Standardize if schema_id is provided
        if schema_id:
            logging.info(f"Standardizing document {file_path.name} (docId={document_id}) with schema: {schema_id}")
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
                    # If 404, doc might not be ready yet, wait and re-check
                    if std_get_resp.status_code == 404:
                        time.sleep(10)
                        continue
                    # Otherwise assume it's done or failed in the background
                    logging.info(f"Standardization request returned status code={std_get_resp.status_code} for "
                                 f"{file_path.name}. (Break polling loop)")
                    break

                logging.info(f"Standardization completed for {file_path.name} with schema: {schema_id}")
            except Exception as e:
                logging.error(f"Standardization failed for {file_path.name}: {str(e)}", exc_info=True)
                raise RuntimeError(f"Standardization failed for {file_path.name}: {str(e)}") from e

        return True

    files_completed = 0
    logging.info(f"Beginning parallel upload for {total_files} files. max_workers={max_workers}")
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
                logging.info(f"Successfully processed {file_path.name} ({files_completed}/{total_files})")

                if progress_callback:
                    progress_callback(files_completed, total_files)

            except Exception as e:
                # We already logged the error above, but let's trigger error_callback too
                if error_callback:
                    error_callback(file_path, str(e))
                else:
                    # Fallback: log again if there's no error callback
                    logging.error(f"Error processing file {file_path.name}: {e}")
