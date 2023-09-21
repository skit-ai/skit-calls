import csv
import tempfile
import time
from typing import Any, Dict, Iterable, List, Optional, Union, Set

import pandas as pd
from loguru import logger

from skit_calls import constants as const
from skit_calls.data import mutators, query
from skit_calls.data.model import Turn


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
    start_date: str,
    end_date: str,
    lang: str,
    domain_url: str,
    org_ids: Optional[Set[str]] = None,
    call_quantity: int = 200,
    call_type: List[str] = [const.INBOUND, const.OUTBOUND],
    use_fsm_url: bool = False,
    ignore_callers: Optional[List[str]] = None,
    reported: bool = False,
    template_id: Optional[int] = None,
    use_case: Optional[str] = None,
    flow_name: Optional[str] = None,
    min_duration: Optional[float] = None,
    asr_provider: Optional[str] = None,
    states: Optional[List[str]] = None,
    intents: Optional[List[str]] = None,
    on_disk: bool = True,
    batch_turns: int = const.TURNS_LIMIT,
    delay: float = const.Q_DELAY,
    timezone: str = const.DEFAULT_TIMEZONE,
) -> Union[str, pd.DataFrame]:
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

    :param lang: A language code.
    :type lang: str

    :param use_fsm_url: Whether to use turn audio url from fsm or s3 path.
    :type use_fsm_url: bool

    :param call_quantity: Number of calls to be fetched, defaults to 200
    :type call_quantity: int, optional

    :param call_type: Pick the environment ('INBOUND' or 'OUTBOUND'), defaults to both
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

    :param states: A list of states that should be picked from sampling, defaults to None
    :type states: Optional[List[str]], optional
    
    :param intents: A list of intents that should be picked from sampling, defaults to None
    :type intents: Optional[List[str]], optional

    :param on_disk: "in-memory" (False) vs "files" (True), defaults to None
    :type on_disk: Optional[str], optional

    :param timezone: Timezone for the sampling, defaults to "Asia/Kolkata"
    :type timezone: str, optional

    :return: A directory path if save is set to "files" otherwise path to a file.
    :rtype: str
    """
    start_time = time.time()
    random_call_ids = query.gen_random_call_ids(
        start_date,
        end_date,
        ids_=org_ids,
        limit=call_quantity,
        call_type=call_type,
        lang=lang,
        min_duration=min_duration,
        template_id=template_id,
        use_case=use_case,
        flow_name=flow_name,
        excluded_numbers=ignore_callers,
        reported=reported,
    )
    logger.info(f"Number of call Ids obtained is {len(random_call_ids)}")
    end_time_first = time.time()
    total_time = str(end_time_first - start_time)
    logger.info(f"Time required to obtain call IDs {total_time} seconds")
    random_call_data = query.gen_random_calls(
        random_call_ids,
        asr_provider=asr_provider,
        intents=intents,
        states=states,
        limit=batch_turns,
        delay=delay,
        domain_url=domain_url,
        use_fsm_url=use_fsm_url,
        timezone=timezone,
    )
    end_time_second = time.time()
    total_time_second_query = str(end_time_second - end_time_first)
    logger.info(f"Time required to obtain call data from queried IDs {total_time_second_query} seconds")
    if on_disk:
        return save_turns_on_disk(random_call_data)
    df = save_turns_in_memory(random_call_data)
    logger.info(f"Number of call with data obtained is {df.shape[0]}")
    return df


def select(
    call_ids: Optional[List[int]] = None,
    org_ids: Optional[Set[int]] = None,
    csv_file: Optional[str] = None,
    uuid_col: Optional[str] = None,
    call_history: bool = False,
    on_disk: bool = True,
    delay: float = const.Q_DELAY
) -> Union[str, pd.DataFrame]:
    """
    Sample calls.

    :param call_ids: A list of call ids.
    :type call_ids: List[int]

    :param on_disk: To save "in-memory" (works for <5k calls) vs "files", defaults to True
    :type on_disk: bool

    :return: A directory path if save is set to "files" otherwise path to a file.
    :rtype: str
    """
    try:
        if csv_file and uuid_col and org_ids:
            df = pd.read_csv(csv_file)
            call_ids = query.get_call_ids_from_uuids(org_ids, tuple(df[uuid_col].unique()))
        else:
            raise ValueError("Both csv_file or uuid_column must be provided.")
        if not call_ids:
            raise ValueError("No call ids or csv file provided.")
        random_call_data = query.gen_random_calls(call_ids, delay=const.Q_DELAY)
        if call_history:
            random_call_data = mutators.add_call_history(random_call_data)
        if on_disk:
            return save_turns_on_disk(random_call_data)
        return save_turns_in_memory(random_call_data)
    except Exception as e:
        logger.error(e)
        logger.error(f"This error is common if you are requesting a large dataset.")
