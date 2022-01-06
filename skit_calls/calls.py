import asyncio
import aiohttp

from skit_calls import constants as const


async def get_call(url: str, jwt: str, params: dict) -> dict:
    """
    Make an HTTP GET request and return the response.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={const.AUTHORIZATION: jwt}, params=params) as response:
            return await response.json()
