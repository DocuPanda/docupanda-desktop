import logging
import time
from typing import Optional

import requests

from dp_desktop.const import Params


def get_files(folder_path):
    all_files = list(folder_path.rglob('*.*'))
    files = [f for f in all_files if f.suffix.lower() in Params.allowed_suffix]
    return all_files, files


def request_with_retries(
        method: str,
        url: str,
        max_retries: int = 10,
        backoff_factor: int = 2,
        max_backoff: int = 600,
        request_timeout: int = 40,
        statuses_to_retry: Optional[set] = None,
        log: Optional[logging.Logger] = None,
        **kwargs
):
    if statuses_to_retry is None:
        statuses_to_retry = {408, 429, 500, 502, 503, 504}

    logger = log if log else logging.getLogger(__name__)

    attempt = 0
    total_sleep_time = 0
    circuit_breaker_limit = max_backoff * 2

    while attempt < max_retries:
        attempt += 1
        try:
            response = requests.request(method, url, **kwargs, timeout=request_timeout)
            if response.status_code in statuses_to_retry:
                logger.warning(f"Request {method} {url} attempt={attempt} failed with "
                               f"status={response.status_code}. Will retry...")
                if attempt < max_retries:
                    sleep_time = min(backoff_factor * (2 ** (attempt - 1)), max_backoff)
                    if total_sleep_time + sleep_time > circuit_breaker_limit:
                        logger.error(f"Circuit breaker triggered: total sleep time {total_sleep_time + sleep_time} "
                                     f"would exceed limit of {circuit_breaker_limit} seconds.")
                        response.raise_for_status()
                    time.sleep(sleep_time)
                    total_sleep_time += sleep_time
                else:
                    logger.error(f"Exhausted retries for {method} {url}. Failing permanently.")
                    response.raise_for_status()
            else:
                response.raise_for_status()
                return response

        except (requests.exceptions.RequestException, ConnectionError, TimeoutError) as exc:
            logger.warning(f"Request {method} {url} attempt={attempt} threw exception: {exc}. Will retry...")
            if attempt == max_retries:
                logger.error(f"Exhausted retries for {method} {url}, last error: {exc}. Failing permanently.")
                raise
            sleep_time = min(backoff_factor * (2 ** (attempt - 1)), max_backoff)
            if total_sleep_time + sleep_time > circuit_breaker_limit:
                logger.error(f"Circuit breaker triggered: total sleep time {total_sleep_time + sleep_time} "
                             f"would exceed limit of {circuit_breaker_limit} seconds.")
                raise Exception(f"Circuit breaker limit exceeded for {method} {url}") from exc
            time.sleep(sleep_time)
            total_sleep_time += sleep_time

    raise RuntimeError(f"Request {method} {url} failed after {max_retries} retries with unknown cause.")
