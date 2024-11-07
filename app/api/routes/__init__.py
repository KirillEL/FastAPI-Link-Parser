from fastapi import APIRouter
from .public import public_router

global_router = APIRouter(
    prefix="/api/v1"
)

global_router.include_router(public_router)

__all__ = ['global_router']
