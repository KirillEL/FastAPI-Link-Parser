from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler import calc_metrics
from app.database import get_db
from .router import crawler_router


@crawler_router.get(
    "/calc_metrics",
    response_model=None
)
async def get_calc_metrics(db: AsyncSession = Depends(get_db)):
    return await calc_metrics(db)
