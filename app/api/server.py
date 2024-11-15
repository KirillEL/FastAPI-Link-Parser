from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from .routes import global_router
from ..redis import redis_service


def init_routes(_app: FastAPI):
    _app.include_router(global_router)


def init_middlewares(_app: FastAPI):
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await redis_service.init_redis()
    await redis_service.delete_visited_urls()
    yield


def create_application():
    _app = FastAPI(
        title="Web Crawler",
        docs_url="/api/v1/docs",
        debug=True,
        lifespan=lifespan
    )
    init_middlewares(_app)
    init_routes(_app)

    return _app


app = create_application()
