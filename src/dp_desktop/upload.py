import base64
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from dp_desktop.utils import request_with_retries

# Constants for timeouts
POST_REQUEST_TIMEOUT = 100  # Seconds each POST/GET can wait before timing out
REQUEST_TIMEOUT = 10  # Seconds each POST/GET can wait before timing out
POLL_TIMEOUT = 900  # Total seconds to wait for a doc to finish uploading/processing
POLL_INTERVAL = 5  # Seconds between status checks


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
    Production-grade uploader for large-scale doc ingestion and (optional) standardization.

    Features:
    - Parallel uploads with ThreadPoolExecutor.
    - Each HTTP request has a hard 10-second timeout to prevent indefinite waiting.
    - Polling each doc's status is capped at 900 seconds total.
    - Standardization (if schema_id is provided) also has a 900-second cap.
    - Detailed logging at each step; every failure is logged at ERROR level.
    - progress_callback(files_completed, total_files) is called after each successful file.
    - error_callback(file_path, error_message) is called on each failure if provided.
    """

    # For demonstration only – replace with your actual file-discovery logic
    def get_files(path: Path):
        all_files = list(path.glob("*"))
        # Example: we’ll just filter by extension here
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.txt', '.tiff', '.tif', '.webp'}
        allowed_files = [f for f in all_files if f.suffix.lower() in allowed_extensions]
        return all_files, allowed_files

    log = logging.getLogger(__name__)

    # 1) Discover valid files
    log.info(f"Scanning folder: {folder_path}")

    allowed_set = {'.pdf', '.jpg', '.jpeg', '.png', '.txt', '.tiff', '.tif', '.webp'}

    all_files, allowed_files = get_files(folder_path)
    total_files = len(allowed_files)

    log.info(f"Found {len(all_files)} total files; {len(allowed_files)} valid files "
             f"(allowed extensions: {allowed_set}).")

    if len(allowed_files) == 0:
        log.info("No valid files to process; returning early.")
        return

    # Let the user/UI know we're at 0 of total_files
    if progress_callback:
        progress_callback(0, total_files)

    # 2) Internal function for single-file upload + poll + (optional) standardize
    def _upload_and_standardize_file(file_path: Path):
        """Upload a single file, poll for completion, optionally standardize, with robust timeouts."""
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-API-Key": api_key
        }

        # --- (A) Upload step ---
        try:
            log.info(f"[UPLOAD START] {file_path.name}")

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

            # Use our retry wrapper for POST
            response = request_with_retries(
                "POST",
                upload_url,
                json=payload,
                headers=headers,
                request_timeout=POST_REQUEST_TIMEOUT,
                log=log
            )
            document_id = response.json().get('documentId')
            if not document_id:
                raise RuntimeError(f"No documentId returned for {file_path.name}")

            log.info(f"[UPLOAD SUCCESS] {file_path.name}, docId={document_id}")

        except Exception as e:
            msg = f"[UPLOAD FAIL] {file_path.name}: {str(e)}"
            log.error(msg, exc_info=True)
            raise RuntimeError(msg) from e

        # --- (B) Poll for doc to reach "completed" within 900 seconds ---
        try:
            doc_get_url = f"https://app.docupanda.io/document/{document_id}"
            start_time = time.time()

            for attempt_i in range(100):
                if (time.time() - start_time) > POLL_TIMEOUT:
                    raise RuntimeError(f"Timeout after {POLL_TIMEOUT}s: doc {document_id} never completed.")

                time.sleep(POLL_INTERVAL)

                # Use our retry wrapper for GET
                get_resp = request_with_retries(
                    "GET",
                    doc_get_url,
                    headers=headers,
                    request_timeout=REQUEST_TIMEOUT,
                    log=log
                )
                status = get_resp.json().get('status')

                if status == 'completed':
                    log.info(f"[DOC COMPLETED] {file_path.name}, docId={document_id}")
                    break
                elif status == 'failed':
                    raise RuntimeError(f"Doc {document_id} failed during processing.")

        except Exception as e:
            msg = f"[DOC POLL FAIL] {file_path.name}: {str(e)}"
            log.error(msg, exc_info=True)
            raise RuntimeError(msg) from e

        # --- (C) Optionally standardize if schema_id was provided ---
        if schema_id:
            try:
                log.info(f"[STANDARDIZE START] {file_path.name}, docId={document_id}, schema={schema_id}")

                std_url = "https://app.docupanda.io/standardize/batch"
                std_payload = {
                    "documentIds": [document_id],
                    "schemaId": schema_id
                }
                std_resp = request_with_retries(
                    "POST",
                    std_url,
                    json=std_payload,
                    headers=headers,
                    request_timeout=REQUEST_TIMEOUT,
                    log=log
                )
                standardization_ids = std_resp.json().get('standardizationIds', [])
                if not standardization_ids:
                    raise RuntimeError(f"No standardizationId returned for doc {document_id}.")
                std_id = standardization_ids[0]

                # (D) Poll for standardization to be "completed" within 900 seconds
                std_get_url = f"https://app.docupanda.io/standardization/{std_id}"
                start_time = time.time()

                for attempt_i in range(100):
                    if (time.time() - start_time) > POLL_TIMEOUT:
                        raise RuntimeError(
                            f"Timeout after {POLL_TIMEOUT}s: standardization {std_id} never completed."
                        )

                    time.sleep(POLL_INTERVAL)
                    # Use our retry wrapper for GET
                    std_get_resp = request_with_retries(
                        "GET",
                        std_get_url,
                        headers=headers,
                        request_timeout=REQUEST_TIMEOUT,
                        log=log
                    )
                    # If the resource doesn't exist yet, keep polling
                    if std_get_resp.status_code == 404:
                        continue

                    # Break on any other success code
                    std_get_resp.raise_for_status()
                    log.info(f"[STANDARDIZE COMPLETE] docId={document_id}, stdId={std_id}")
                    break

            except Exception as e:
                msg = f"[STANDARDIZE FAIL] {file_path.name}, docId={document_id}: {str(e)}"
                log.error(msg, exc_info=True)
                raise RuntimeError(msg) from e

        return True  # Return success to the caller

    # 3) Run all files in parallel
    log.info(f"Beginning parallel processing of {total_files} files. max_workers={max_workers}")

    files_completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(_upload_and_standardize_file, f): f for f in allowed_files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()  # Raises if any error occurred
                files_completed += 1

                log.info(f"[FILE DONE] {file_path.name} ({files_completed}/{total_files})")
                if progress_callback:
                    progress_callback(files_completed, total_files)

            except Exception as e:
                # Already logged, but let UI know if possible
                if error_callback:
                    error_callback(file_path, str(e))
                else:
                    log.error(f"[FILE ERROR] {file_path.name}: {e}")

    log.info(f"All tasks completed. Processed={files_completed}, Skipped={total_files - files_completed}.")
