from fastapi import APIRouter
from .crawler import crawler_router

public_router = APIRouter(
    prefix=""
)

public_router.include_router(crawler_router)
