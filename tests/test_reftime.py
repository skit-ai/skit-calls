
from skit_calls.data.model import get_readable_reftime

def test_reftime_examples():

    reftime_without_tz = "2022-12-01T10:37:43.039748+00:00"
    readable_reftime_with_tz = get_readable_reftime(reftime_without_tz)
    assert readable_reftime_with_tz == "01-Dec-2022 04:07 PM"

    reftime_with_tz = "2023-01-07T15:08:04.861674+05:30"
    readable_reftime_with_tz = get_readable_reftime(reftime_with_tz)
    assert readable_reftime_with_tz == "07-Jan-2023 03:08 PM"

