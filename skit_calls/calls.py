import tempfile
import csv
from typing import Iterable, List, Optional, Any, Dict

import pandas as pd
from loguru import logger
from psycopg2.errors import SerializationFailure

from skit_calls.data import query
from skit_calls.data.model import Turn
from skit_calls import constants as const


def save_turns_in_memory(stream: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(list(stream))


def save_turns_on_disk(stream: Iterable[Dict[str, Any]]) -> str:
    _, file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
    with open(file_path, "w", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=Turn.__slots__)
        writer.writeheader()
        for turn in stream:
            writer.writerow(turn)
    return file_path


def sample(
    org_id: str,
    start_date: str,
    end_date: str,
    lang: str,
    call_quantity: int = 200,
    call_type: str = const.INBOUND,
    ignore_callers: Optional[List[str]] = None,
    reported: bool = False,
    use_case: Optional[str] = None,
    flow_name: Optional[str] = None,
    min_duration: Optional[float] = None,
    asr_provider: Optional[str] = None,
    on_disk: bool = True,
) -> str | pd.DataFrame:
    """
    Sample calls.

    :param url: The endpoint for fetching call and related data.
    :type url: str

    :param token: An auth token.
    :type token: str

    :param start_date: A start date for the sampling.
    :type start_date: str

    :param end_date: An end date for the sampling.
    :type end_date: str

    :param lang_code: A language code.
    :type lang_code: str

    :param call_quantity: Number of calls to be fetched, defaults to 200
    :type call_quantity: int, optional

    :param call_type: Pick the environment (live or subtesting), defaults to const.LIVE
    :type call_type: str, optional

    :param ignore_callers: A list of callers that should be ignored from sampling, defaults to None
    :type ignore_callers: Optional[List[str]], optional

    :param reported: If True filter only reported calls, defaults to True
    :type reported: bool, optional

    :param resolved: If True filter only resolved calls, defaults to True
    :type resolved: bool, optional

    :param custom_search_key: Custom search filter key, defaults to None
    :type custom_search_key: Optional[str], optional

    :param custom_search_value: Value for custom search filter key, defaults to None
    :type custom_search_value: Optional[str], optional

    :param inflate: To "in-memory" (works for <5k calls) vs "files", defaults to None
    :type save: Optional[str], optional

    :return: A directory path if save is set to "files" otherwise path to a file.
    :rtype: str
    """
    try:
        random_call_ids = query.gen_random_call_ids(
            org_id,
            start_date,
            end_date,
            limit=call_quantity,
            call_type=call_type,
            lang=lang,
            min_duration=min_duration,
            use_case=use_case,
            flow_name=flow_name,
            excluded_numbers=ignore_callers,
            reported=reported,
        )()
        random_call_data = query.gen_random_calls(
            random_call_ids,
            asr_provider=asr_provider,
        )
        if on_disk:
            return save_turns_on_disk(random_call_data)
        return save_turns_in_memory(random_call_data)
    except SerializationFailure as e:
        logger.error(e)
        logger.error(f"This error is common if you are requesting a large dataset.")
