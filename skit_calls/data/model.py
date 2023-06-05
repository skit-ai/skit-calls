import json
import os
import pytz

import pandas as pd

from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import unquote, urljoin
import boto3
from botocore.exceptions import ClientError

import attr

from skit_calls import constants as const

MaybeString = Optional[str]
MaybeFloat = Optional[float]
Thing = Dict[str, Any]
Things = Optional[List[Thing]]

IntentName = MaybeString
IntentScore = MaybeFloat
Slots = Things
Entities = Things
Utterances = Things

S3_CLIENT = boto3.client('s3', aws_access_key_id=const.AWS_ACCESS_KEY_ID, aws_secret_access_key=const.AWS_SECRET_ACCESS_KEY, aws_session_token=None)


def prediction2intent(prediction: Thing) -> Tuple[IntentName, IntentScore, Slots]:
    intents = prediction.get(const.INTENTS, [])
    if not intents:
        return None, None, []
    intent, *_ = intents
    return intent[const.NAME], intent[const.SCORE], intent[const.SLOTS]


def slots2entities(slots: Slots) -> Entities:
    return [entity for slot in slots for entity in slot.get(const.VALUES, [])]


def jsonify_utterances(json_string: MaybeString) -> Optional[Thing]:
    if not json_string:
        return None
    utterances = json.loads(json_string)
    if isinstance(utterances, list) and utterances:
        if all(isinstance(utterance, list) for utterance in utterances):
            return utterances
        if all(isinstance(utterance, dict) for utterance in utterances):
            return [utterances]
    return None

def format_utterances(json_string: MaybeString) -> MaybeString:
    req_utterances: str = lambda utterances: "\n".join([alternative[const.TRANSCRIPT] for alternative in utterances])
    utterances = jsonify_utterances(json_string)
    if not utterances:
        return None
    if isinstance(utterances, list):
        if isinstance(utterances[0], list):
            return req_utterances(utterances[0])
        if isinstance(utterances[0], dict):
            return req_utterances(utterances)
    return None

def extract_primary_utterance(json_string: MaybeString) -> MaybeString:
    utterances = jsonify_utterances(json_string)
    if not utterances:
        return None
    if isinstance(utterances, list):
        if isinstance(utterances[0], list):
            return utterances[0][0][const.TRANSCRIPT]
        if isinstance(utterances[0], dict):
            return utterances[0][const.TRANSCRIPT]
    return None

def jsonify_maybestr(json_string: MaybeString) -> Optional[Thing]:
    if not json_string:
        return None
    if isinstance(json_string, dict):
        return json_string
    return json.loads(json_string)


def float_maybestr(string: MaybeString) -> MaybeFloat:
    if not string:
        return None
    return float(string)


def print_floats(val: MaybeFloat) -> str:
    return f"{val:.2f}" if val else "None"


def print_utterance(utterances: Utterances) -> str:
    if not utterances:
        return "None"
    return utterances[0][0][const.TRANSCRIPT]

def extract_bot_response(json_str: MaybeString) -> MaybeString:
    return jsonify_maybestr(json_str).get(const.BOT_RESPONSE, None) if json_str else None

def get_call_url(
    base: MaybeString, path: MaybeString, extension: MaybeString = None
) -> MaybeString:
    if not path:
        return None
    return urljoin(os.path.join(base, ""), unquote(path).lstrip("/")) + extension


def generate_presigned_url(s3_client: boto3.client, client_method, method_parameters, expires_in):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action.

    :param s3_client: A Boto3 Amazon S3 client.
    :param client_method: The name of the client method that the URL performs.
    :param method_parameters: The parameters of the specified client method.
    :param expires_in: The number of seconds the presigned URL is valid for.
    :return: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params=method_parameters,
            ExpiresIn=expires_in
        )
    except ClientError:
        raise ValueError("Couldn't get a presigned URL for params '%s'.", method_parameters)
    return url


def get_url(
    base: MaybeString,
    path: MaybeString,
    call_uuid: str,
    domain_url: str,
    use_fsm_url: bool = False
) -> MaybeString:
    # when use_fsm_url is False -> get audio url from s3
    # else use presigned url to get audio from s3
    
    audio_url = urljoin(os.path.join(base, ""), unquote(path).lstrip("/"))
    if use_fsm_url:
        bucket = audio_url.split("amazonaws.com/")[-1].split("/")[0]
        key = unquote(path).lstrip("/")
        presigned_url = generate_presigned_url(
            s3_client=S3_CLIENT,
            client_method='get_object',
            method_parameters={'Bucket': bucket, 'Key': key},
            expires_in=604800 # 7 days
        )
        return presigned_url
    
    return audio_url


def get_readable_reftime(reftime: str) -> str:

    timestamp_with_tz = pd.to_datetime(reftime)

    if str(timestamp_with_tz.tz) == str(pytz.UTC):
        new_tz = const.DEFAULT_TIMEZONE
        timestamp_with_tz = timestamp_with_tz.astimezone(new_tz)

    return timestamp_with_tz.strftime("%d-%b-%Y %I:%M %p")

@attr.s(slots=True, weakref_slot=False)
class Turn:
    call_id: str = attr.ib(kw_only=True, repr=True, converter=str)
    call_uuid: str = attr.ib(kw_only=True, repr=False)
    conversation_id: int = attr.ib(kw_only=True, repr=True, converter=int)
    conversation_uuid: str = attr.ib(kw_only=True, repr=False)
    audio_url: str = attr.ib(kw_only=True, repr=False)
    reftime: str = attr.ib(kw_only=True, converter=datetime.isoformat, repr=False)
    readable_reftime : str = attr.ib(kw_only=True)
    state: str = attr.ib(kw_only=True, repr=False)

    utterances: Utterances = attr.ib(
        kw_only=True, factory=list, converter=jsonify_utterances, repr=print_utterance
    )
    format_utterances: MaybeString = attr.ib(
        kw_only=True, factory=str, converter=format_utterances, repr=False
    )
    primary_utterance: MaybeString = attr.ib(
        kw_only=True, factory=str, converter=extract_primary_utterance, repr=False
    )
    context: Optional[Thing] = attr.ib(
        kw_only=True, factory=dict, converter=jsonify_maybestr, repr=False
    )
    bot_response: MaybeString = attr.ib(kw_only=True, default=None, converter=extract_bot_response, repr=False)

    intents_info: Things = attr.ib(
        kw_only=True, factory=list, converter=jsonify_maybestr, repr=False
    )

    prediction: Thing = attr.ib(
        kw_only=True, factory=dict, converter=jsonify_maybestr, repr=False
    )

    intent: IntentName = attr.ib(kw_only=True, default=None)
    intent_score: IntentScore = attr.ib(kw_only=True, default=None, repr=print_floats)
    slots: Slots = attr.ib(kw_only=True, factory=list, repr=False)
    entities: Entities = attr.ib(kw_only=True, factory=list, repr=False)

    call_url: MaybeString = attr.ib(kw_only=True, repr=False, default=None)
    call_type: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    language: MaybeString = attr.ib(kw_only=True, default=None)
    asr_provider: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    call_end_status: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    disposition: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    virtual_number: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    flow_version: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    flow_id: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    flow_name: MaybeString = attr.ib(kw_only=True, default=None, repr=False)
    flow_uuid: str = attr.ib(kw_only=True, repr=False)

    template_id: str = attr.ib(kw_only=True, repr=True, converter=str)

    client_uuid: str = attr.ib(kw_only=True, repr=False)

    asr_latency: MaybeFloat = attr.ib(
        kw_only=True, default=None, converter=float_maybestr, repr=False
    )
    slu_latency: MaybeFloat = attr.ib(
        kw_only=True, default=None, converter=float_maybestr, repr=False
    )
    call_duration: MaybeFloat = attr.ib(
        kw_only=True, default=None, converter=float_maybestr, repr=False
    )

    @classmethod
    def from_record(cls, record: namedtuple, domain_url: str, use_fsm_url: bool = False, timezone: str = const.DEFAULT_TIMEZONE) -> "Turn":
        intent_name, intent_score, slots = prediction2intent(record.prediction or {})
        entities = slots2entities(slots)
        call_url = record.call_url or get_call_url(
            os.getenv(const.CDN_RECORDINGS_BASE_PATH),
            record.call_url_id,
            const.WAV_FILE,
        )
        audio_url = get_url(record.turn_audio_base_path, record.turn_audio_path, record.call_uuid, domain_url, use_fsm_url)
        reftime = record.reftime.astimezone(pytz.timezone(timezone))
        readable_reftime = get_readable_reftime(reftime)
        return cls(
            call_id=record.call_id,
            call_uuid=record.call_uuid,
            conversation_id=record.conversation_id,
            conversation_uuid=record.conversation_uuid,
            audio_url=audio_url,
            call_url=call_url,
            call_type=record.call_type,
            disposition=record.disposition,
            reftime=reftime,
            readable_reftime=readable_reftime,
            state=record.state,
            prediction=record.prediction,
            utterances=record.utterances,
            primary_utterance=record.utterances,
            format_utterances=record.utterances,
            context=record.context,
            bot_response=record.context,
            call_end_status=record.call_end_status,
            intents_info=record.intents_info,
            intent=intent_name,
            intent_score=intent_score,
            slots=slots,
            entities=entities,
            language=record.language,
            asr_latency=record.asr_latency,
            slu_latency=record.slu_latency,
            asr_provider=record.asr_provider,
            virtual_number=record.virtual_number,
            flow_version=record.flow_version,
            flow_id=record.flow_id,
            flow_name=record.flow_name,
            flow_uuid=record.flow_uuid,
            template_id=record.template_id,
            call_duration=record.call_duration,
            client_uuid=record.client_uuid,
        )

    def serialize(self, _, __, value):
        return (
            json.dumps(value, ensure_ascii=False)
            if isinstance(value, (dict, list))
            else value
        )

    def to_dict(self) -> Dict[str, Any]:
        return attr.asdict(self, value_serializer=self.serialize)
