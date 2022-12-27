import os
import time
from pprint import pformat
from typing import Any, Dict, Iterable, Set, Tuple, Optional, List

from loguru import logger
from psycopg2.extensions import connection as Conn
from psycopg2.extras import NamedTupleCursor
from tqdm import tqdm
from psycopg2.errors import SerializationFailure, OperationalError

from skit_calls import constants as const
from skit_calls.data.db import connect, postgres
from skit_calls.data.model import Turn


def as_turns(records, domain_url, on_prem) -> Iterable[Dict[str, Any]]:
    for record in records:
        yield Turn.from_record(record, domain_url, on_prem).to_dict()


def get_query(query_name):
    with open(os.getenv(query_name)) as handle:
        return handle.read()


def gen_random_call_ids(
    id_: int,
    start_date: str,
    end_date: str,
    limit: int = const.DEFAULT_CALL_QUANTITY,
    call_type: List[str] = [const.INBOUND, const.OUTBOUND],
    reported: bool = False,
    use_case: Optional[str] = None,
    lang: Optional[str] = None,
    flow_name: Optional[str] = None,
    min_duration: Optional[float] = None,
    excluded_numbers: Optional[Set[str]] = None,
    retry_limit: int = 2,
):
    excluded_numbers = set(excluded_numbers) or set()
    excluded_numbers = excluded_numbers.union(const.DEFAULT_IGNORE_CALLERS_LIST)
    reported_status = 0 if reported else None
    call_filters = {
        const.END_DATE: end_date,
        const.START_DATE: start_date,
        const.ID: id_,
        const.CALL_TYPE: tuple(call_type),
        const.RESOLVED: reported_status,
        const.LANG: lang,
        const.EXCLUDED_NUMBERS: tuple(excluded_numbers),
        const.MIN_AUDIO_DURATION: min_duration,
        const.USE_CASE: use_case,
        const.FLOW_NAME: flow_name,
        const.LIMIT: limit + const.MARGIN * limit,
    }

    logger.debug(f"call_filters={pformat(call_filters)} | {limit=}")

    query = get_query(const.RANDOM_CALL_ID_QUERY)

    tries = 0
    call_ids = ()
    
    while tries <= retry_limit:
        try:
            with connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, call_filters)
                    all_ids = cursor.fetchall()
                    return tuple(id_[0] for id_ in all_ids)
        except OperationalError as e:
                logger.warning(e)
                logger.warning("retrying to fetch call ids")
                time.sleep(2)
                tries += 1
                if tries > retry_limit:
                    raise ValueError("retry limit exceeded for this query to get call ids")
    
    return call_ids


def get_call_ids_from_uuids(id_: int, uuids: Tuple[str]) -> Tuple[int]:
    query = get_query(const.CALL_IDS_FROM_UUIDS_QUERY)
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, {const.UUID: uuids, const.ID: id_})
            return tuple(id_[0] for id_ in cursor.fetchall())


def gen_random_calls(
    call_ids: Tuple[int],
    asr_provider: Optional[str] = None,
    states: Optional[Set[str]] = None,
    limit: int = const.TURNS_LIMIT,
    delay: float = const.Q_DELAY,
    domain_url: str = const.DEFAULT_AUDIO_URL_DOMAIN,
    on_prem: bool = False,
):
    time.sleep(1)
    query = get_query(const.RANDOM_CALL_DATA_QUERY)
    states = tuple(set(states or [None]))
    turn_filters = {
        const.ASR_PROVIDER: asr_provider,
        const.CONVERSATION_TYPES: (const.UCASE_INPUT,),
        const.CONVERSATION_SUB_TYPES: (const.UCASE_AUDIO,),
        const.STATES: states,
    }
    logger.debug(f"call_filters={pformat(turn_filters)}")

    call_id_size = len(call_ids)
    batch_size = (
        call_id_size // limit
        if call_id_size % limit == 0
        else call_id_size // limit + 1
    )
    logger.debug(f"Creating {batch_size} batches for {call_id_size} calls")
    i = 0

    with tqdm(total=batch_size, desc="Downloading turns for calls dataset.") as pbar:
        while i < call_id_size:
            batch = call_ids[i : i + limit]
            try:
                with connect() as conn:
                    with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                        cursor.execute(query, {**turn_filters, const.CALL_IDS: batch})
                        result_set = cursor.fetchall()
                        yield from as_turns(result_set, domain_url, on_prem)
                        pbar.update(1)
                i += limit
            except (SerializationFailure, OperationalError) as e:
                logger.error(e)
                logger.error(f"This error is common if you are requesting a large dataset. We will retry the batch in a while.")
                time.sleep(delay)
