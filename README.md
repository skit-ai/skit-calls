# skit-calls

Skit.ai's calls library.

We provide means to sample calls, and conversations (aka turns) from a specified environment.
This data is required for analysis and training machine learning models. Hence the current offering
of this library is an aggregation of conversation over calls.

Let's look at the schema for calls, we get the following from the `/call_report/calls/?sort=desc&page=1&page_size=20&call_type=live` endpoint.

```python
{
  "call_audio": str,
  "created_at": Optional[str],                          # 2022-01-07 15:04:01.941288 +0000 UTC
  "deleted_at": Optional[str],
  "end_state": str,                                     # "TRANSFER_AGENT"
  "flow_version": str,                                  # "3.0.12"
  "is_reported": bool,                                  # False
  "language_code": str,                                 # en
  "report_details": Optional[str],
  "status": str,                                        # "TRANSFER"
  "total_call_duration": Optional[float],               # 0.0
  "type": str,                                          # INBOUND
  "updated_at": str,                                    # 2022-01-07 15:04:01.941288 +0000 UTC
  "uuid": str,
  "viva_call_duration": float                           # 5.824208627
}
```

... and here's a representation of a call with conversations (aka turns) within, we get the following from the `https://apigateway.vernacular.ai/call_report/calls/some-call-id/` endpoint.

```python
{
  "call_audio": "",
  "caller_number": str, # "00000000",
  "conversations": [
    {
      "bot": str,
      "current_intent": None,
      "debug_metadata": {},
      "errors": [],
      "language_switch": None,
      "metadata": dict,
      "nlsml": "COF_en",
      "state": "COF",
      "sub_type": "TTS",
      "trigger_trail": [
        "_remote_replacement_"
      ],
      "type": str, # "RESPONSE"
      "uuid": str
    },
    {
      "audio_path": "xyz.flac",
      "audio_url": "https://bucket.com/bucket/xyz.flac",
      "bot": str,
      "current_intent": None,
      "cycle_duration": {
        "asr": float,
        "asr_from_source": float,
        "asr_processing": float,
        "asr_to_dest": float,
        "plute": float
      },
      "debug_metadata": {
        "plute_request": {
          "alternatives": [
            {
              "am_score": float,
              "confidence": float,
              "lm_score": float,
              "transcript": str, # "no"
            }
          ],
          "context": {
            "ack_slots": [],
            "asr_provider": str # "vernacular"
            "bot_response": str,
            "call_uuid": str,
            "current_intent": "",
            "current_state": str,
            "smalltalk": true,
            "uuid": str,
            "virtual_number": str # "000000"
          },
          "short_utterance": {},
          "text": "no"
        }
      },
      "errors": [],
      "metadata": dict,
      "slots_filled": None,
      "state": str, # "COF"
      "sub_type": str, # "AUDIO"
      "trigger_name": str # "_cancel_"
      "type": str, # "INPUT"
      "user": str, # "no"
      "uuid": str
    },
  ],
  "created_at": str, # "2022-01-07 14:56:47.162929 +0000 UTC"
  "current_plute_version": str, # "err"
  "deleted_at": None,
  "end_state": str, # "TRANSFER_AGENT",
  "errors": [],
  "flow_version": str, # "3.0.12"
  "is_reported": None,
  "issues_reported": None,
  "language_code": str, # "en"
  "report_details": None,
  "status": str, # "TRANSFER"
  "total_call_duration": None,
  "type": str, # "INBOUND"
  "updated_at": str, # "2022-01-07 14:56:47.162929 +0000 UTC"
  "uuid": str,
  "virtual_number": str, # "000000",
  "viva_call_duration": float # 25.214965607
}
```

We see that the `conversations` field contains the exchange between voice-bot and a person. We can notice familiar fields from the calls schema. Given our purpose of analysis and training models, we decided to move the call related fields within each conversation turn. In other words, we return a list of conversation turns with call information supplied by their parent (call). 

Finally, we save the above data in csv files. In case we need to download really large datasets, over 1M data points we can use `inflate="files"` to prevent OOM.
In this case, we save each call as a standalone csv on disk. This makes it easy to ensure data is not lost by running something like:

```shell
ls /tmp/calls-dir | wc -l
```

This library isn't responsible for pre-processing and removing unwanted fields. [skit-df](https://github.com/skit-ai/skit-df) is a library that handles those responsibilities.

## Installation
The library uses `python=^3.9`.

```shell
pip install skit-calls
skit-calls -h
```

## Usage

This library comes with a wide set of filters for filtering conversations.

```
❯ skit-calls -h
usage: skit-calls [-h] --start-date START_DATE --lang LANG [--url URL] [--token TOKEN]
                  [--end-date END_DATE] [--timezone TIMEZONE]
                  [--call-quantity CALL_QUANTITY] [--call-type {live,subtesting}]
                  [--ignore-callers [IGNORE_CALLERS ...]] [--reported] [--resolved]
                  [--save {files,in-memory}]
                  {custom-search} ...

Skit.ai's calls library. We provide means to sample calls and conversations from a specified
environment. Learn about this library at: https://github.com/skit-ai/skit-calls

positional arguments:
  {custom-search}
    custom-search       Calls API custom search options.

optional arguments:
  -h, --help            show this help message and exit
  --start-date START_DATE
                        Search calls made after the given date (YYYY-MM-DD).
  --lang LANG           Search calls made in the given language.
  --url URL             The url of the skit.ai's api gateway.
  --token TOKEN         The auth token from https://github.com/skit-ai/skit-auth.
  --end-date END_DATE   Search calls made before the given date.
  --timezone TIMEZONE   The timezone to use for the start and end dates.
  --call-quantity CALL_QUANTITY
                        The number of calls to filter.
  --call-type {live,subtesting}
                        The type of call to filter. One of ("live", "subtesting")
  --ignore-callers [IGNORE_CALLERS ...]
                        A comma separated list of callers to ignore.
  --reported            Search only reported calls.
  --resolved            Search only resolved calls.
  --save {files,in-memory}
                        Choose to inflate calls in memory or in files. Recommended to use
                        files if data points are over 1M.
```

We also have access to the `custom-search`, allows querying a few (_otherwise_) obscure fields, namely: `flow_name`, `virtual_number`, `old_state`, `tts_provider`, etc.

```
❯ skit-calls custom-search -h
usage: skit-calls custom-search [-h] --key KEY --value VALUE

optional arguments:
  -h, --help     show this help message and exit
  --key KEY      Search custom fields using the `custom_search_key` var.
  --value VALUE  Search custom fields using the `custom_search_value` var.
```

The default url is the production api gateway endpoint.

## Example

Sharing a few invocation examples:

We can use the [skit-auth](https://github.com/skit-ai/skit-auth) project to get an auth token.
The token can be passed as an argument...

```shell
skit-calls --start-date=2022-01-01 --end-date=2022-01-05 --lang=hi --token="ajsonwebtoken"
```

... or we can pipe the auth command to skit-calls.

```shell
skit-auth --email iam@skit.ai --password --org-id 2 | skit-calls --start-date=2022-01-01 --end-date=2022-01-05 --lang=hi
```

and an example with custom search:

```shell
skit-auth --email iam@skit.ai --password --org-id 2 | skit-calls \
    --start-date=2022-01-01 \
    --end-date=2022-01-05 \
    --lang=hi \
    custom-search --key=usecase --value=some_usecase
```

We read the token from `~/.skit/token` if it exists. So one can avoid the pipe or passing the long token as an argument if the 
skit-auth command has already been run once. **Do note, the organization where the calls are fetched from, comes from the token.**
