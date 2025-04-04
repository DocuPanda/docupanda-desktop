import dataclasses
from pathlib import Path

import requests


@dataclasses.dataclass
class Document:
    documentId: str
    filename: str
    fileExtension: str


def download_dataset(api_key: str,
                     dataset_name: str,
                     output_dir: Path):
    """
    Download a dataset (placeholder).

    :param api_key: Your API key
    :param dataset_name: Name of the dataset to download
    :param output_dir: Local folder where the dataset should be saved
    """

    all_documents = list_documents(api_key, dataset_name)
    for doc in all_documents:
        url = f"https://app.docupanda.io/document/{doc.documentId}/download/ocr-url?hours=6"

        headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            download_url = result.get('url')
            if download_url:
                # Download the file
                file_response = requests.get(download_url)
                if file_response.status_code == 200:
                    # Save the file to the output directory
                    output_path = (output_dir / (doc.filename + '.pdf'))
                    with open(output_path, 'wb') as f:
                        f.write(file_response.content)
                    print(f"Downloaded: {output_path}")
                else:
                    print(f"Failed to download file from {download_url}")
            else:
                print("No download URL found in response.")

            # download all standardizations

            url = "https://app.docupanda.io/standardizations?document_id=docId&limit=20&offset=0&exclude_payload=false"

            headers = {
                "accept": "application/json",
                "X-API-Key": "api_key"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                stds = response.json()[0:1]
                # get the first standardization if exists
                std = stds[0] if stds else None
                if std:
                    standardization_dict = std['data']
                    # write it with the same filename as document, and .json extension
                    output_path = output_dir / f"{doc.filename}.json"
                    with open(output_path, 'w') as f:
                        f.write(standardization_dict)

        # get all standardizations that belong to this document and download the latest one as json


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
            "X-API-Key": api_key  # Use the user-provided API key
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx responses

        new_documents = response.json()

        # If empty or less than limit, this is the last batch
        if not new_documents:
            break

        for doc in new_documents:
            all_documents.append(
                Document(
                    documentId=doc['documentId'],
                    filename=doc['filename'],
                    fileExtension=doc['fileExtension']  # Use fileExtension instead of filetype
                )
            )

        offset += limit

        # If we received fewer than the limit, we've reached the final page
        if len(new_documents) < limit:
            break
    # Example usage: save or process the documents in the desired directory
    # (currently just printing the total count)
    print(f"Total documents fetched: {len(all_documents)}")
    return all_documents
