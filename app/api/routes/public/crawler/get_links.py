from http import HTTPStatus

import aiohttp

from app.crawler import get_links
from .router import crawler_router
from fastapi import Request
import app.dto.responses as responses
from app.redis import redis_service


@crawler_router.get(
    "/links",
    response_model=responses.GetLinksResponse,
    status_code=HTTPStatus.OK
)
async def get_links_from_url(request: Request, url: str):
    await redis_service.delete_visited_urls()
    async with aiohttp.ClientSession() as session:
        links = await get_links(session, url=url)
    validated_model = responses.GetLinksResponse.model_validate({
        "links": links
    })
    return validated_model
