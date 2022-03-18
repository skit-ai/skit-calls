import argparse
import tempfile
import os
import sys
from datetime import datetime
from typing import Tuple

import pytz

from skit_calls import __version__, calls
from skit_calls import constants as const
from skit_calls import utils


def to_datetime(date_string: str) -> datetime:
    """
    Check if date_string is in YYYY-MM-DD format.

    :param date_string: A string representing a date in YYYY-MM-DD format.
    :type date_string: [type]
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: expected YYYY-MM-DD for {date_string} instead, {e}"
        )


def validate_date_ranges(start_date: datetime, end_date: datetime) -> None:
    """
    Check if start_date is before end_date.

    :param start_date: A datetime object representing a former date.
    :type start_date: datetime
    :param end_date: A datetime object representing a latter date.
    :type end_date: datetime
    """
    if start_date > end_date:
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        raise ValueError(f"{start_date=} shouldn't be later than {end_date=}.")


def process_date_filters(
    start_date: datetime, end_date: datetime, timezone: str = const.DEFAULT_TIMEZONE
) -> Tuple[str, str]:
    """
    Process the date filters.

    Make timestamps timezone aware and provide their ISO-8601 representation.

    :param start_date: A datetime object representing a former date.
    :type start_date: datetime
    :param end_date: A datetime object representing a latter date.
    :type end_date: datetime
    :param timezone: The timezone to use for the start and end dates.
    :type timezone: str
    """
    start_date = start_date.replace(tzinfo=pytz.timezone(timezone)).isoformat()
    end_date = end_date.replace(
        hour=23, minute=59, tzinfo=pytz.timezone(timezone)
    ).isoformat()
    return start_date, end_date


def get_version():
    return __version__


def build_cli():
    version = get_version()
    parser = argparse.ArgumentParser(
        description=const.DESCRIPTION.format(version={version})
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=3, help="Increase verbosity"
    )
    parser.add_argument(
        "--lang",
        type=str,
        help="Search calls made in the given language.",
        required=True,
    )
    parser.add_argument(
        "--org-id",
        type=str,
        help="The org for which you need the data.",
    )
    parser.add_argument(
        "--start-date",
        type=to_datetime,
        required=True,
        help="Search calls made after the given date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=to_datetime,
        help="Search calls made before the given date.",
        default=datetime.now(),
    )
    parser.add_argument(
        "--timezone",
        type=str,
        help="The timezone to use for the start and end dates.",
        default=const.DEFAULT_TIMEZONE,
    )
    parser.add_argument(
        "--call-quantity",
        type=int,
        help="The number of calls to filter.",
        default=const.DEFAULT_CALL_QUANTITY,
    )
    parser.add_argument(
        "--call-type",
        type=str,
        help='The type of call to filter.',
        default=const.INBOUND,
        choices=[const.INBOUND, const.OUTBOUND, const.CALL_TEST],
    )
    parser.add_argument(
        "--ignore-callers",
        type=str,
        nargs="*",
        help="A comma separated list of callers to ignore.",
        default=const.DEFAULT_IGNORE_CALLERS_LIST,
    )
    parser.add_argument(
        "--reported", action="store_true", help="Search only reported calls."
    )
    parser.add_argument(
        "--use-case", help="Filter calls by use-case."
    )
    parser.add_argument(
        "--flow-name", help="Filter calls by flow-name."
    )
    parser.add_argument(
        "--audio-duration", type=float, help="Filter calls with greater than audio duration."
    )
    parser.add_argument(
        "--asr-provider", help="Filter calls served via a specific ASR provider."
    )
    parser.add_argument(
        "--on-disk",
        action="store_true",
        help="Each record is written directly to disk. Highly recommended for large queries.",
        default=True,
    )
    return parser


def cmd_to_str(args: argparse.Namespace) -> str:
    utils.configure_logger(args.verbose)
    validate_date_ranges(args.start_date, args.end_date)
    args.start_date, args.end_date = process_date_filters(
        args.start_date, args.end_date
    )
    if args.token is None:
        is_pipe = not os.isatty(sys.stdin.fileno())
        if is_pipe:
            args.token = sys.stdin.readline().strip()
        else:
            raise argparse.ArgumentTypeError(
                "Expected to receive --token=<token> or its valued piped in."
            )
    maybe_df = calls.sample(
        args.org_id,
        args.start_date,
        args.end_date,
        args.lang,
        call_quantity=args.call_quantity,
        call_type=args.call_type,
        ignore_callers=args.ignore_callers,
        reported=args.reported,
        use_case=args.use_case,
        flow_name=args.flow_name,
        audio_duration=args.audio_duration,
        asr_provider=args.asr_provider,
        on_disk=args.on_disk,
    )
    if args.on_disk:
        print(maybe_df)
    else:
        _, file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
        maybe_df.to_csv(file_path, index=False)
        print(file_path)


def main() -> None:
    """
    Main entry point for the CLI.

    - We try to read token from the pipes if not passed as an arguments.
    - Process the request for sampling calls.
    - Collect the results:
        - In a single file if save is set to IN_MEMORY.
            - Print the file path to stdout.
        - In multiple files if save is set to FILES.
            - Print the directory path to stdout.
    """
    cmd_to_str(build_cli().parse_args())
