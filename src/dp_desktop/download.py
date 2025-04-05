import dataclasses
import logging
from pathlib import Path
from typing import Optional, Callable
import threading
import requests
import concurrent.futures
import json


@dataclasses.dataclass
class Document:
    documentId: str
    filename: str
    fileExtension: str


def download_dataset(
        api_key: str,
        dataset_name: str,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        error_callback: Optional[Callable[[str, str], None]] = None
):
    """
    Download a dataset with progress/error callbacks.

    - Lists the documents in the given dataset (list_documents)
    - Downloads each doc's PDF and (optionally) standardization data
    - Logs progress, successes, and errors
    - Calls progress_callback(docs_completed, total_docs) after each doc finishes
    - Calls error_callback(doc_label, error_message) on any failure
    """

    logging.info(f"Starting download of dataset='{dataset_name}' to: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_documents = list_documents(api_key, dataset_name)
    total_docs = len(all_documents)
    logging.info(f"Total docs to download: {total_docs}")

    if total_docs == 0:
        logging.info("No documents found for this dataset. Returning.")
        return

    progress_lock = threading.Lock()
    docs_completed = [0]  # mutable reference for closure

    # Initialize callback at 0
    if progress_callback:
        progress_callback(0, total_docs)

    def download_single(doc: Document):
        """Download PDF + standardization data for a single doc."""
        doc_label = f"{doc.filename} ({doc.documentId})"
        logging.info(f"Starting download for: {doc_label}")

        headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }
        try:
            # 1) Get a short-lived OCR download URL
            url = f"https://app.docupanda.io/document/{doc.documentId}/download/ocr-url?hours=6"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            download_url = result.get('url')
            if not download_url:
                raise RuntimeError("No download URL found in response.")

            # 2) Download the PDF file
            file_response = requests.get(download_url)
            file_response.raise_for_status()
            output_path = output_dir / (doc.filename + '.pdf')
            with open(output_path, 'wb') as f:
                f.write(file_response.content)
            logging.info(f"Downloaded PDF to: {output_path}")

            # 3) Download standardizations (if any)
            stds_url = (
                f"https://app.docupanda.io/standardizations"
                f"?document_id={doc.documentId}&limit=20&offset=0&exclude_payload=false"
            )
            stds_resp = requests.get(stds_url, headers=headers)
            stds_resp.raise_for_status()
            stds = stds_resp.json()

            # If there's standardization data, save the first standardization payload
            if stds:
                std = stds[0]
                standardization_dict = std.get('data')
                if standardization_dict:
                    json_path = output_dir / f"{doc.filename}.json"
                    with open(json_path, 'w') as f:
                        json.dump(standardization_dict, f, indent=2)
                    logging.info(f"Downloaded standardization JSON to: {json_path}")

            logging.info(f"Finished download for: {doc_label}")

        except Exception as e:
            logging.error(f"Error downloading doc {doc_label}: {e}", exc_info=True)
            if error_callback:
                error_callback(doc_label, str(e))

        finally:
            # Update progress, whether success or error
            with progress_lock:
                docs_completed[0] += 1
                if progress_callback:
                    progress_callback(docs_completed[0], total_docs)

    # Use a thread pool for parallel downloads
    max_workers = 5
    logging.info(f"Creating ThreadPoolExecutor with max_workers={max_workers}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(download_single, all_documents)

    logging.info(f"All downloads completed. Documents processed: {docs_completed[0]} / {total_docs}")


def list_documents(api_key: str, dataset_name: str):
    """
    Query DocuPanda for all documents in a dataset (paginated).
    Returns a list of Document objects.
    """
    logging.info(f"Listing all documents for dataset='{dataset_name}'")
    limit = 1000
    offset = 0
    all_documents = []

    while True:
        url = (
            "https://app.docupanda.io/documents"
            f"?dataset={dataset_name}"
            f"&limit={limit}"
            f"&offset={offset}"
            "&exclude_payload=true"
        )

        headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            new_documents = response.json()
            if not new_documents:
                break

            for doc in new_documents:
                all_documents.append(
                    Document(
                        documentId=doc['documentId'],
                        filename=doc['filename'],
                        fileExtension=doc['fileExtension']
                    )
                )
            offset += limit

            if len(new_documents) < limit:
                break

        except Exception as e:
            logging.error(f"Error fetching documents for dataset='{dataset_name}': {e}", exc_info=True)
            break

    logging.info(f"Total documents fetched: {len(all_documents)}")
    return all_documents
