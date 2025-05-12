import dataclasses
from typing import List

import requests


@dataclasses.dataclass
class Schema:
    schemaName: str
    schemaId: str


def list_schemas(api_key: str) -> List[Schema]:
    url = "https://app.docupanda.io/schemas?limit=1000&offset=0&exclude_payload=true"

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    schemas = response.json()
    return [Schema(schemaName=schema['schemaName'], schemaId=schema['schemaId']) for schema in schemas]


def list_dataset_names(api_key: str) -> List[str]:
    url = "https://app.docupanda.io/dataset-names"

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    datasets = response.json()['datasetNames']
    return datasets
