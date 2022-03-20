import os
import time
import random
from pprint import pformat
from typing import Any, Dict, Tuple, Set, Iterable

from loguru import logger
from psycopg2.extensions import connection as Conn
from psycopg2.extras import NamedTupleCursor

from skit_calls import constants as const
from skit_calls.data.model import Turn
from skit_calls.data.db import postgres, connect


def as_turns(records) -> Iterable[Dict[str, Any]]:
    for record in records:
        yield Turn.from_record(record).to_dict()


def get_query(query_name):
    with open(os.environ[query_name]) as handle:
        return handle.read()


def gen_random_call_ids(
    id_: int,
    start_date: str,
    end_date: str,
    limit: int = const.DEFAULT_CALL_QUANTITY,
    call_type: str = const.INBOUND,
    reported: bool = False,
    use_case: str | None = None,
    lang: str | None = None,
    flow_name: str | None = None,
    min_duration: float | None = None,
    excluded_numbers: Set[str] | None = None,
):
    excluded_numbers = set(excluded_numbers) or set()
    excluded_numbers = excluded_numbers.union(const.DEFAULT_IGNORE_CALLERS_LIST)
    reported_status = 0 if reported else None
    call_filters = {
        const.END_DATE: end_date,
        const.START_DATE: start_date,
        const.ID: id_,
        const.CALL_TYPE: call_type,
        const.RESOLVED: reported_status,
        const.LANG: lang,
        const.EXCLUDED_NUMBERS: tuple(excluded_numbers),
        const.MIN_AUDIO_DURATION: min_duration,
        const.USE_CASE: use_case,
        const.FLOW_NAME: flow_name,
    }

    logger.debug(f"call_filters={pformat(call_filters)} | {limit=}")

    query = get_query(const.RANDOM_CALL_ID_QUERY)

    @postgres()
    def on_connect(conn: Conn):
        with conn.cursor() as cursor:
            cursor.execute(query, call_filters)
            all_ids = cursor.fetchall()
            some_ids = random.sample(all_ids, limit) if len(all_ids) > limit else all_ids
        return tuple(id_[0] for id_ in some_ids)
    return on_connect


def gen_random_calls(
    call_ids: Tuple[int],
    asr_provider: str | None = None,
    limit: int  = const.TURNS_LIMIT
):
    time.sleep(1)
    query = get_query(const.RANDOM_CALL_DATA_QUERY)
    turn_filters = {
        const.ASR_PROVIDER: asr_provider,
        const.CONVERSATION_TYPES: (const.UCASE_INPUT,),
        const.CONVERSATION_SUB_TYPES: (const.UCASE_AUDIO,),
    }

    call_id_size = len(call_ids)
    batch_size = call_id_size // limit if call_id_size % limit == 0 else call_id_size // limit + 1
    logger.debug(f"Creating {batch_size} batches for {call_id_size} calls")
    batch_no = 0
    for i in range(0, len(call_ids), limit):
        batch = call_ids[i:i+limit]
        with connect() as conn:
            with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                logger.debug(f"\n[{batch_no + 1}/{batch_size}] turn_filters=\n{pformat(turn_filters)}\n for {len(batch)} call-ids.")
                cursor.execute(query, {**turn_filters, const.CALL_IDS: batch})
                result_set = cursor.fetchall()
                yield from as_turns(result_set)
                batch_no += 1
        time.sleep(0.5)
