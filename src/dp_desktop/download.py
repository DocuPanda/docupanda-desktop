import dataclasses
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


def download_dataset(api_key: str,
                     dataset_name: str,
                     output_dir: Path,
                     progress_callback: Optional[Callable[[int, int], None]] = None,
                     error_callback: Optional[Callable[[str, str], None]] = None):
    """
    Download a dataset with progress/error callbacks.
    """

    all_documents = list_documents(api_key, dataset_name)
    total_docs = len(all_documents)

    progress_lock = threading.Lock()
    docs_completed = [0]  # Use mutable object to be shared among threads

    if progress_callback:
        progress_callback(0, total_docs)

    def download_single(doc: Document):
        nonlocal docs_completed
        doc_label = f"{doc.filename} ({doc.documentId})"
        try:
            headers = {
                "accept": "application/json",
                "X-API-Key": api_key
            }

            url = f"https://app.docupanda.io/document/{doc.documentId}/download/ocr-url?hours=6"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            download_url = result.get('url')
            if not download_url:
                raise RuntimeError("No download URL found in response.")

            file_response = requests.get(download_url)
            file_response.raise_for_status()
            output_path = (output_dir / (doc.filename + '.pdf'))
            with open(output_path, 'wb') as f:
                f.write(file_response.content)
            print(f"Downloaded: {output_path}")

            # Download standardizations
            stds_url = (
                f"https://app.docupanda.io/standardizations"
                f"?document_id={doc.documentId}&limit=20&offset=0&exclude_payload=false"
            )
            stds_resp = requests.get(stds_url, headers=headers)
            stds_resp.raise_for_status()
            stds = stds_resp.json()
            if stds:
                std = stds[0]
                standardization_dict = std.get('data')
                if standardization_dict:
                    json_path = output_dir / f"{doc.filename}.json"
                    with open(json_path, 'w') as f:
                        json.dump(standardization_dict, f, indent=2)

        except Exception as e:
            if error_callback:
                error_callback(doc_label, str(e))
            else:
                print(f"Error downloading doc {doc_label}: {e}")
        finally:
            with progress_lock:
                docs_completed[0] += 1
                if progress_callback:
                    progress_callback(docs_completed[0], total_docs)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_single, all_documents)

    print(f"Total documents processed: {docs_completed[0]}")


def list_documents(api_key, dataset_name):
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

    print(f"Total documents fetched: {len(all_documents)}")
    return all_documents
