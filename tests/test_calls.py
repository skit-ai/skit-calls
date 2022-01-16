import json
import os
import shutil

import aiohttp
import pytest
from aioresponses import aioresponses

from skit_calls import calls
from skit_calls import constants as const

FAKE_CONVERSATIONS = [
    {
        const.UUID: "fake_conv_uuid_1",
        const.PREDICTION: json.dumps(["fake_predictions"]),
        const.METADATA: json.dumps(["fake_metadata"]),
        const.CREATED_AT: "2022-01-10",
        const.UPDATED_AT: "2022-01-11T00:00:00.000+05:30",
    },
    {const.UUID: "fake_call_uuid_2"},
]


def test_build_call_tag_filter():
    assert const.ALL == calls.build_call_tag_filter(reported=True, resolved=True)
    assert const.REPORTED == calls.build_call_tag_filter(reported=True, resolved=False)
    assert const.RESOLVED == calls.build_call_tag_filter(reported=False, resolved=True)
    assert const.ALL == calls.build_call_tag_filter(reported=False, resolved=False)


def test_get_auth_header():
    fake_token = "faketoken"
    fake_auth_header = calls.get_auth_header(fake_token)
    assert fake_auth_header == {const.AUTHORIZATION: f"Bearer {fake_token}"}


def test_get_full_range():
    current_page = 10
    total_pages = 100
    full_range = calls.get_full_range(current_page, total_pages)
    assert isinstance(full_range, range)
    assert full_range.start == current_page
    assert full_range.stop == total_pages + 1


def test_get_sampled_range():
    current_page = 10
    total_pages = 100
    sample_size = 50
    sampled_range = calls.get_sampled_range(current_page, total_pages, sample_size)
    assert isinstance(sampled_range, list)
    assert len(sampled_range) == sample_size


def test_get_pages_to_read():
    current_page = 10
    total_pages = 100
    smaller_sample_size = 50
    bigger_sample_size = 150
    smaller_pages_to_read = calls.get_pages_to_read(
        current_page, total_pages, smaller_sample_size
    )
    bigger_pages_to_read = calls.get_pages_to_read(
        current_page, total_pages, bigger_sample_size
    )
    assert bigger_pages_to_read == calls.get_full_range(current_page, total_pages)
    assert len(smaller_pages_to_read) == len(
        calls.get_sampled_range(current_page, total_pages, smaller_sample_size)
    )


# def test_to_isoformat():
#     from datetime import datetime

#     iso_date = "2022-01-10"
#     grainer_iso_date = "2022-01-10T00:00:00.000+05:30"
#     not_iso_date = "10012022"

#     assert datetime.fromisoformat(calls.to_isoformat(iso_date))
#     assert datetime.fromisoformat(calls.to_isoformat(grainer_iso_date))
#     pytest.raises(ValueError, calls.to_isoformat, not_iso_date)


@pytest.mark.asyncio
async def test_inflate_call():
    empty_calls_response = {const.ITEMS: []}
    fake_call_uuid = "fake_call_uuid"
    fake_call_route = const.ROUTE__TURN.format(fake_call_uuid)
    fake_calls_response = {
        const.ITEMS: [
            {
                const.UUID: fake_call_uuid,
            }
        ]
    }
    with aioresponses() as mockedSession:
        mockedSession.get(
            fake_call_route,
            status=200,
            payload={
                const.ITEMS: [],
                const.CONVERSATIONS: FAKE_CONVERSATIONS,
            },
        )
        session = aiohttp.ClientSession()
        inflated_turns = await calls.inflate_call(session, fake_calls_response)
        assert [] == await calls.inflate_call(session, empty_calls_response)
        assert not any(
            [
                const.UUID in turn or const.CONVERSATIONS in turn
                for turn in inflated_turns
            ]
        )
        await session.close()


@pytest.mark.asyncio
async def test_get():
    page_no = 10
    fake_path = "http://fake-console.skit.ai"
    fake_call_uuid = "fake_call_uuid"
    fake_call_route = const.ROUTE__TURN.format(fake_call_uuid)

    with aioresponses() as mockedSession:
        mockedSession.get(
            fake_path,
            status=200,
            payload={
                const.ITEMS: [
                    {
                        const.UUID: fake_call_uuid,
                        const.CONVERSATIONS: FAKE_CONVERSATIONS,
                    }
                ],
            },
        )
        mockedSession.get(
            fake_call_route,
            status=200,
            payload={const.ITEMS: [], const.CONVERSATIONS: FAKE_CONVERSATIONS},
        )
        session = aiohttp.ClientSession()
        fake_calls_response = await calls.get(session, fake_path, {}, page_no)
        assert isinstance(fake_calls_response, dict)
        assert const.ITEMS in fake_calls_response
        assert not any(
            [
                const.UUID in turn or const.CONVERSATIONS in turn
                for turn in fake_calls_response.get(const.ITEMS)
            ]
        )
        await session.close()


@pytest.mark.asyncio
async def test_get_metadata():
    fake_params = {"param1": "value1", "param2": "value2"}
    fake_base_url = "http://fake-console.skit.ai"
    fake_query = "?param1=value1&param2=value2"
    fake_path = f"{const.ROUTE__CALL}{fake_query}"
    fake_token = "fake_token"
    fake_headers = calls.get_auth_header(fake_token)
    with aioresponses() as mockedSession:
        mockedSession.get(
            fake_path,
            status=200,
            headers={**fake_headers},
            payload={"testkey": "testvalue"},
        )
        metadata_response = await calls.get_metadata(
            fake_base_url, fake_token, fake_params
        )
        assert isinstance(metadata_response, dict)
        assert "testkey" in metadata_response
        assert metadata_response["testkey"] == "testvalue"


@pytest.mark.asyncio
async def test_inflate_calls_in_memory():
    fake_params = {"param1": "value1", "param2": "value2"}
    fake_pages = [10, 11, 12, 13, 14]
    fake_base_url = "http://fake-console.skit.ai"
    fake_token = "fake_token"
    fake_call_uuid = "fake_call_uuid"
    fake_call_route = const.ROUTE__TURN.format(fake_call_uuid)
    fake_headers = calls.get_auth_header(fake_token)

    with aioresponses() as mockedSession:
        for p_no in fake_pages:
            fake_query = f"?page={p_no}&param1=value1&param2=value2"
            fake_path = f"{const.ROUTE__CALL}{fake_query}"
            mockedSession.get(
                fake_path,
                status=200,
                headers={**fake_headers},
                payload={
                    const.ITEMS: [
                        {
                            const.UUID: fake_call_uuid,
                            const.CONVERSATIONS: FAKE_CONVERSATIONS,
                        }
                    ],
                },
            )
            mockedSession.get(
                fake_call_route,
                status=200,
                headers={**fake_headers},
                payload={const.ITEMS: [], const.CONVERSATIONS: FAKE_CONVERSATIONS},
            )
        calls_list = await calls.inflate_calls_in_memory(
            fake_base_url, fake_token, fake_params, pages_to_read=fake_pages
        )
        assert len(calls_list) == (len(FAKE_CONVERSATIONS) * len(fake_pages))
        assert not any(
            [const.UUID in turn or const.CONVERSATIONS in turn for turn in calls_list]
        )


def test_save_call():
    fake_turns = [
        {
            "prediction": ["fake_predictions"],
            "metadata": ["fake_metadata"],
            "created_at": "2022-01-10T00:00:00",
            "updated_at": "2022-01-11T00:00:00+05:30",
            "conversation_uuid": "fake_conv_uuid_1",
            "call_uuid": "fake_call_uuid",
            "items": [],
        },
        {
            "created_at": None,
            "updated_at": None,
            "conversation_uuid": "fake_conv_uuid_2",
            "call_uuid": "fake_call_uuid",
            "items": [],
        },
    ]
    tmp_file_path = calls.save_call("/tmp", fake_turns)
    assert os.path.exists(tmp_file_path)
    os.remove(tmp_file_path)


@pytest.mark.asyncio
async def test_inflate_calls_in_files():
    fake_params = {"param1": "value1", "param2": "value2"}
    fake_pages = [10, 11, 12, 13, 14]
    fake_base_url = "http://fake-console.skit.ai"
    fake_token = "fake_token"
    fake_call_uuid = "fake_call_uuid"
    fake_call_route = const.ROUTE__TURN.format(fake_call_uuid)
    fake_headers = calls.get_auth_header(fake_token)

    with aioresponses() as mockedSession:
        for p_no in fake_pages:
            fake_query = f"?page={p_no}&param1=value1&param2=value2"
            fake_path = f"{const.ROUTE__CALL}{fake_query}"
            mockedSession.get(
                fake_path,
                status=200,
                headers={**fake_headers},
                payload={
                    const.ITEMS: [
                        {
                            const.UUID: fake_call_uuid,
                            const.CONVERSATIONS: FAKE_CONVERSATIONS,
                        }
                    ],
                },
            )
            mockedSession.get(
                fake_call_route,
                status=200,
                headers={**fake_headers},
                payload={const.ITEMS: [], const.CONVERSATIONS: FAKE_CONVERSATIONS},
            )
        saved_calls_dir = await calls.inflate_calls_in_files(
            fake_base_url, fake_token, fake_params, pages_to_read=fake_pages
        )
        assert os.path.exists(saved_calls_dir)
        assert len(os.listdir(saved_calls_dir)) == len(fake_pages)
        shutil.rmtree(saved_calls_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_sample():
    fake_base_url = "http://fake-console.skit.ai"
    fake_token = "fake_token"
    start_date = "11012022"
    end_date = "12012022"
    lang_code = "hi"
    call_type = const.LIVE
    ignore_callers = const.DEFAULT_IGNORE_CALLERS_LIST
    reported = True
    resolved = True
    call_quantity = 400
    custom_search_key = None
    custom_search_value = None
    save = const.IN_MEMORY

    fake_call_uuid = "fake_call_uuid"
    fake_call_route = const.ROUTE__TURN.format(fake_call_uuid)
    fake_metadata_response = {
        const.TOTAL_ITEMS: 10,
        const.PAGE: 3,
        const.TOTAL_PAGES: 20,
    }
    empty_metadata_response = {
        const.TOTAL_ITEMS: 0,
    }

    fake_query = f"?{const.CALL_TYPE}={call_type}&{const.END_DATE}={end_date}&{const.IGNORED_CALLER_NUMBERS}={ignore_callers[1]}&{const.IGNORED_CALLER_NUMBERS}={ignore_callers[0]}&{const.LANG_CODE}={lang_code}&{const.PAGE_SIZE}=1&{const.START_DATE}={start_date}&{const.TAB}={calls.build_call_tag_filter(reported, resolved)}"
    fake_call_path = f"{const.ROUTE__CALL}{fake_query}"
    fake_headers = calls.get_auth_header(fake_token)
    with aioresponses() as mockedSession:
        mockedSession.get(
            fake_call_path,
            status=200,
            headers={**fake_headers},
            payload=empty_metadata_response,
        )
        mockedSession.get(
            fake_call_path,
            status=200,
            headers={**fake_headers},
            payload=fake_metadata_response,
        )
        for p_no in range(
            fake_metadata_response[const.PAGE],
            fake_metadata_response[const.TOTAL_PAGES] + 1,
        ):
            fake_query = f"?{const.CALL_TYPE}={call_type}&{const.END_DATE}={end_date}&{const.IGNORED_CALLER_NUMBERS}={ignore_callers[1]}&{const.IGNORED_CALLER_NUMBERS}={ignore_callers[0]}&{const.LANG_CODE}={lang_code}&{const.PAGE}={p_no}&{const.PAGE_SIZE}=1&{const.START_DATE}={start_date}&{const.TAB}={calls.build_call_tag_filter(reported, resolved)}"
            fake_call_path = f"{const.ROUTE__CALL}{fake_query}"
            mockedSession.get(
                fake_call_path,
                status=200,
                headers={**fake_headers},
                payload={
                    const.ITEMS: [
                        {
                            const.UUID: fake_call_uuid,
                            const.CONVERSATIONS: FAKE_CONVERSATIONS,
                        }
                    ],
                },
            )
            mockedSession.get(
                fake_call_route,
                status=200,
                headers={**fake_headers},
                payload={const.ITEMS: [], const.CONVERSATIONS: FAKE_CONVERSATIONS},
            )
        with pytest.raises(ValueError):
            await calls.sample(
                fake_base_url,
                fake_token,
                start_date,
                end_date,
                lang_code,
                call_quantity,
                call_type,
                ignore_callers,
                reported,
                resolved,
                custom_search_key,
                custom_search_value,
                save,
            )
        sampled_calls_path = await calls.sample(
            fake_base_url,
            fake_token,
            start_date,
            end_date,
            lang_code,
            call_quantity,
            call_type,
            ignore_callers,
            reported,
            resolved,
            custom_search_key,
            custom_search_value,
            save,
        )
        assert os.path.exists(sampled_calls_path)
        shutil.rmtree(sampled_calls_path, ignore_errors=True)
