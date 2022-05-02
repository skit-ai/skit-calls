# skit-calls

Skit.ai's calls library.

We provide means to sample calls, and conversations (aka turns) from a specified environment.
This data is required for analysis and training machine learning models. Hence the current offering
of this library is an aggregation of conversation over calls.

We use this project as a component within [skit-pipelines](https://github.com/skit-ai/skit-pipelines)

## Installation

The installation is a little quirky because it is meant for usage within a separate project [here](https://github.com/skit-ai/skit-pipelines).
You would need credentials from skit.ai to get past dvc pull and beyond.

```bash
git clone git@github.com:skit-ai/skit-calls.git
cd skit-calls

# Highly recommended to create a virtual env or use one.
poetry install
dvc pull
source secrets/env.sh
```

## Usage

Post installation, we can see what the tooling provides by running:

```
skit-calls -h

usage: skit-calls [-h] [-v] [--on-disk] {sample,select} ...

Skit.ai's calls library {'0.2.8'}. We provide means to sample calls and conversations
from a specified environment. Learn about this library at: https://github.com/skit-
ai/skit-calls

positional arguments:
  {sample,select}  Supported means to obtain calls datasets aggregated with their turns.
    sample         Random sample calls with a variety of call/turn filters.
    select         Select calls from known call-ids.

options:
  -h, --help       show this help message and exit
  -v, --verbose    Increase verbosity
  --on-disk        Each record is written directly to disk. Highly recommended for large
                   queries.
```

To get random samples:

```bash
❯ poetry run skit-calls sample -h
usage: skit-calls sample [-h] --lang LANG [--org-id ORG_ID] --start-date START_DATE
                         [--end-date END_DATE] [--timezone TIMEZONE]
                         [--call-quantity CALL_QUANTITY]
                         [--call-type {INBOUND,OUTBOUND,CALL_TEST}]
                         [--ignore-callers [IGNORE_CALLERS ...]] [--reported]
                         [--use-case USE_CASE] [--flow-name FLOW_NAME]
                         [--min-audio-duration MIN_AUDIO_DURATION]
                         [--asr-provider ASR_PROVIDER]

options:
  -h, --help            show this help message and exit
  --lang LANG           Search calls made in the given language.
  --org-id ORG_ID       The org for which you need the data.
  --start-date START_DATE
                        Search calls made after the given date (YYYY-MM-DD).
  --end-date END_DATE   Search calls made before the given date.
  --timezone TIMEZONE   The timezone to use for the start and end dates.
  --call-quantity CALL_QUANTITY
                        The number of calls to filter.
  --call-type {INBOUND,OUTBOUND,CALL_TEST}
                        The type of call to filter.
  --ignore-callers [IGNORE_CALLERS ...]
                        A comma separated list of callers to ignore.
  --reported            Search only reported calls.
  --use-case USE_CASE   Filter calls by use-case.
  --flow-name FLOW_NAME
                        Filter calls by flow-name.
  --min-audio-duration MIN_AUDIO_DURATION
                        Filter calls longer than given duration.
  --asr-provider ASR_PROVIDER
                        Filter calls served via a specific ASR provider.
```

But if you already have a selected call-ids in mind:

```bash
usage: skit-calls select [-h] [--call-ids CALL_IDS [CALL_IDS ...]] [--history]

options:
  -h, --help            show this help message and exit
  --call-ids CALL_IDS [CALL_IDS ...]
                        The call-ids to select.
  --history             Collect call history for each turn
```
