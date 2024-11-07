import asyncio

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.crawler import get_links, crawl
from app.database import get_db
from .router import crawler_router
from fastapi import Request, Depends, BackgroundTasks
import app.dto.responses as responses


async def background_crawl(url: str, db: AsyncSession):
    async with aiohttp.ClientSession() as session:
        await crawl(url, db, session)


@crawler_router.post(
    "/start",
    response_model=responses.CrawlerResponse,
    status_code=status.HTTP_200_OK
)
async def start_crawler(request: Request, url: str, background_tasks: BackgroundTasks,
                        db: AsyncSession = Depends(get_db)):
    background_tasks.add_task(background_crawl, url, db)
    return {"message": "Crawling started!"}
