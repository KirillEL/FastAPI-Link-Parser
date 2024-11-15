import aiohttp
from fastapi import Body

from app.crawler import get_words
from .router import crawler_router




@crawler_router.post(
    "/words",
    response_model=list[tuple] | None
)
async def get_words_on_url(url: str = Body(...)):
    async with aiohttp.ClientSession() as session:
        words = await get_words(session=session,url=url)
    return words