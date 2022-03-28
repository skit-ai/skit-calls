import os
import shutil
import pandas as pd

import pytest

from skit_calls import calls
from skit_calls import constants as const

FAKE_DATA = {
    "org_id": "43",
    "start_date": "2022-01-01",
    "end_date": "2022-01-02",
    "lang": "fake_lang",
    "call_quantity": 400,
    "call_type": const.LIVE,
    "ignore_callers": const.DEFAULT_IGNORE_CALLERS_LIST,
    "reported": True,
    "use_case": "fake_use_case",
    "flow_name": "fake_flow_name",
    "min_duration": 1.0,
    "asr_provider": "fake_asr_provider",
}

@pytest.mark.parametrize("args",[FAKE_DATA])
def test_sample_on_disk(args):
    sampled_calls_path = calls.sample(**args, on_disk=True)
    assert os.path.exists(sampled_calls_path)
    shutil.rmtree(sampled_calls_path, ignore_errors=True)

@pytest.mark.parametrize("args",[FAKE_DATA])
def test_sample_in_memory(args):
    sample_calls_df = calls.sample(**args, on_disk=False)
    assert isinstance(sample_calls_df, pd.DataFrame)
