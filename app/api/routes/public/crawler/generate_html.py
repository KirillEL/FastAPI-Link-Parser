from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler import generate_html_report
from app.database import get_db
from .router import crawler_router



@crawler_router.get(
    "/html_page",
    response_model=None
)
async def get_generated_html_file(db: AsyncSession = Depends(get_db)):
    return await generate_html_report(db)