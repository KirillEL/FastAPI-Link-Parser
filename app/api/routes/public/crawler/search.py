from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler import populate_matchrows
from app.database import get_db
from .router import crawler_router
from pydantic import BaseModel, Field
from fastapi import Body, Depends


class SearchRequest(BaseModel):
    first_word: str
    second_word: str



@crawler_router.post(
    "/search",
    response_model=None
)
async def search_words(body: SearchRequest = Body(...), db: AsyncSession = Depends(get_db)):
    return await populate_matchrows(body.first_word, body.second_word, db)


