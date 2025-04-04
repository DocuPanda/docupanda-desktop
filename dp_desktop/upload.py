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
    Upload and standardize all files in parallel, 5 at a time.
    Mark each file as 'done' only after it has been both uploaded and standardized.
    Update UI (progress_callback) as each file finishes, and call error_callback on failures.

    Args:
        folder_path (Path): Directory containing files to upload.
        api_key (str): API authentication key.
        dataset_name (str): Name of the dataset to associate with each file.
        schema_id (Optional[str]): Schema identifier, if applicable.
        progress_callback (Callable[[int, int], None], optional): Function receiving
            (files_completed, total_files) every time a file is done.
        error_callback (Callable[[Path, str]], optional): Function receiving
            (file_path, error_message) in case of error.
        max_workers (int): Number of worker threads for concurrency, default=5.
    """

    files = list(folder_path.rglob('*.*'))  # Adjust filtering as needed
    #  only accept PDF jpg, png, '.txt'
    allowed_set = {'.pdf', '.jpg', '.jpeg', '.png', '.txt'}
    files = [f for f in files if f.suffix.lower() in allowed_set]

    # only pdf, jpg, png files

    total_files = len(files)
    if total_files == 0:
        return  # No files; nothing to do.

    progress_callback(0, total_files)

    # Internal function to handle upload + standardization for a single file
    def _upload_and_standardize_file(file_path: Path):
        """
        Uploads a file, polls DocuPanda until upload is 'completed', then standardizes the file
        (if schemaId is provided), and waits until that standardization is completed.
        Returns normally if successful; raises Exception on any error.
        """

        # 1) Encode and POST the file
        try:
            with open(file_path, 'rb') as f:
                file_contents = base64.b64encode(f.read()).decode()

            # POST to /document
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
            # If there's an error in the upload step, propagate up
            raise RuntimeError(f"Upload failed for {file_path}: {str(e)}") from e

        # 2) Poll until the document status is "completed"
        try:
            doc_get_url = f"https://app.docupanda.io/document/{document_id}"
            while True:
                time.sleep(2)  # Wait a bit between polls
                get_resp = requests.get(doc_get_url, headers=headers)
                get_resp.raise_for_status()
                status = get_resp.json().get('status')
                if status == 'completed':
                    break
                elif status == 'failed':
                    raise RuntimeError(f"DocuPanda processing failed for docId={document_id}")
                # else it's still processing, continue polling
        except Exception as e:
            raise RuntimeError(f"Polling document status failed for {file_path}: {str(e)}") from e

        # 3) If schemaId is provided, standardize the doc
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
                std_get_url = f"https://app.docupanda.io/standardize/{standardization_id}"
                while True:
                    time.sleep(2)
                    std_get_resp = requests.get(std_get_url, headers=headers)
                    std_get_resp.raise_for_status()
                    std_status = std_get_resp.json().get('status')
                    if std_status == 'completed':
                        break
                    elif std_status == 'failed':
                        raise RuntimeError(
                            f"Standardization failed for docId={document_id}, schemaId={schema_id}"
                        )
                    # else keep polling
            except Exception as e:
                raise RuntimeError(f"Standardization failed for {file_path}: {str(e)}") from e

        # If we reach here, the file is done (uploaded + standardized)
        return True

    # We'll submit each file to a ThreadPoolExecutor with up to max_workers=5
    files_completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(_upload_and_standardize_file, file_path): file_path
            for file_path in files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()  # This will raise if _upload_and_standardize_file() failed
                files_completed += 1
                if progress_callback:
                    progress_callback(files_completed, total_files)
            except Exception as e:
                # If there's an error, call error_callback
                if error_callback:
                    error_callback(file_path, str(e))
                else:
                    # If no error_callback is provided, at least raise
                    # or log. For example:
                    print(f"Error processing file {file_path}: {e}")
                # We continue processing other files rather than halting all.
