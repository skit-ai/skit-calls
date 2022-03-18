import imp
import time
import pydash as py_
from skit_calls.data import query
from loguru import logger


def fetch_ids(n, start="2021-01-01", end="2021-12-31", org_id=2):
    s = time.time()
    random_call_ids = query.gen_random_call_ids(
        org_id,
        start,
        end,
        limit=n
    )()
    logger.debug(f"Ran in est {time.time() - s:.2f}s. Got {len(random_call_ids)} call ids.")
    return random_call_ids


def fetch_data(n, start="2021-01-01", end="2021-12-31", org_id=2):
    s = time.time()
    df = []
    try:
        random_call_data = query.gen_random_calls(fetch_ids(n, start=start, end=end, org_id=org_id))
        for item in random_call_data:
            df.append(item)
    except Exception as e:
        print(type(e))
        print(e)
    df = py_.flattern(df)
    logger.debug(f"Ran in est {time.time() - s:.2f}s. | Fetched {len(df)} turns.")
    return df
