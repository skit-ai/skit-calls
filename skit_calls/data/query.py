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


def as_turns(records, domain_url, use_fsm_url, timezone) -> Iterable[Dict[str, Any]]:
    for record in records:
        yield Turn.from_record(record, domain_url, use_fsm_url, timezone).to_dict()


def get_query(query_name):
    with open(os.getenv(query_name)) as handle:
        return handle.read()


def gen_random_call_ids(
    start_date: str,
    end_date: str,
    ids_: Optional[Set[str]] = None,
    limit: int = const.DEFAULT_CALL_QUANTITY,
    call_type: List[str] = [const.INBOUND, const.OUTBOUND],
    reported: bool = False,
    use_case: Optional[str] = None,
    lang: Optional[str] = None,
    template_id: Optional[int] = None,
    flow_name: Optional[str] = None,
    flow_id:  Optional[Set[str]] = [],
    min_duration: Optional[float] = None,
    excluded_numbers: Optional[Set[str]] = None,
    retry_limit: int = 2,
    random_id_limit: int = const.DEFAULT_CALL_QUANTITY,
):
    excluded_numbers = set(excluded_numbers) or set()
    
    if not ids_:
        ids_ = None
        
    logger.info(f"Org id = {ids_}")
    logger.info(f"Template id = {template_id}")
    
    excluded_numbers = excluded_numbers.union(const.DEFAULT_IGNORE_CALLERS_LIST)
    reported_status = 0 if reported else None
    call_filters = {
        const.END_DATE: end_date,
        const.START_DATE: start_date,
        const.ID: ids_,
        const.CALL_TYPE: tuple(call_type),
        const.RESOLVED: reported_status,
        const.LANG: lang,
        const.EXCLUDED_NUMBERS: tuple(excluded_numbers),
        const.MIN_AUDIO_DURATION: min_duration,
        const.USE_CASE: use_case,
        const.FLOW_NAME: flow_name,
        const.LIMIT: limit + const.MARGIN * limit,
        const.TEMPLATE_ID: template_id,
        const.FLOW_ID: flow_id,
        const.RANDOM_ID_LIMT: random_id_limit
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


def get_call_ids_from_uuids(uuids: Tuple[str], ids_: Optional[Set[int]]) -> Tuple[int]:
    query = get_query(const.CALL_IDS_FROM_UUIDS_QUERY)
    ids_ = set(ids_) or set()
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, {const.UUID: uuids, const.ID: ids_})
            return tuple(id_[0] for id_ in cursor.fetchall())


def gen_random_calls(
    call_ids: Tuple[int],
    asr_provider: Optional[str] = None,
    intents: Optional[Set[str]] = None,
    states: Optional[Set[str]] = None,
    limit: int = const.TURNS_LIMIT,
    delay: float = const.Q_DELAY,
    domain_url: str = const.DEFAULT_AUDIO_URL_DOMAIN,
    use_fsm_url: bool = False,
    timezone: str = const.DEFAULT_TIMEZONE,
):
    time.sleep(1)
    query = get_query(const.RANDOM_CALL_DATA_QUERY)
    states = tuple(set(states or [None]))
    intents = tuple(set(intents or [None]))
    turn_filters = {
        const.ASR_PROVIDER: asr_provider,
        const.CONVERSATION_TYPES: (const.UCASE_INPUT,),
        const.CONVERSATION_SUB_TYPES: (const.UCASE_AUDIO,),
        const.STATES: states,
        const.INTENTS: intents,
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
                        yield from as_turns(result_set, domain_url, use_fsm_url, timezone)
                        pbar.update(1)
                i += limit
            except (SerializationFailure, OperationalError) as e:
                logger.error(e)
                logger.error(f"This error is common if you are requesting a large dataset. We will retry the batch in a while.")
                time.sleep(delay)
